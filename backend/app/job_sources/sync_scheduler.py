"""
Sync Scheduler — coordinates sync executions, retries, and updates logs.
Sprint 13: Framework.
"""
import asyncio
import logging
import uuid
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.job_sources.provider_registry import ProviderRegistry
from app.job_sources.rate_limiter import ProviderRateLimiter
from app.job_sources.provider_health import ProviderHealthService
from app.job_sources.sync_audit import SyncAudit
from app.job_sources.ingestion_service import JobIngestionService
from app.job_sources.models import ProviderConfig, ProviderLock, FailedSyncJob

logger = logging.getLogger(__name__)


class ProviderLockService:
    @staticmethod
    async def acquire_lock(db: AsyncSession, provider_name: str, timeout_seconds: int, worker_id: str) -> bool:
        now = datetime.now(timezone.utc)
        stmt = select(ProviderLock).where(ProviderLock.provider_name == provider_name).with_for_update()
        res = await db.execute(stmt)
        lock = res.scalar_one_or_none()
        
        if lock:
            locked_until_naive = lock.locked_until.replace(tzinfo=None) if lock.locked_until.tzinfo else lock.locked_until
            now_naive = now.replace(tzinfo=None) if now.tzinfo else now
            if locked_until_naive > now_naive:
                return False
            # Clean up stale lock
            await db.delete(lock)
            await db.commit()
            
            lock = ProviderLock(
                provider_name=provider_name,
                locked_until=now + timedelta(seconds=timeout_seconds),
                locked_by=worker_id
            )
            db.add(lock)
        else:
            lock = ProviderLock(
                provider_name=provider_name,
                locked_until=now + timedelta(seconds=timeout_seconds),
                locked_by=worker_id
            )
            db.add(lock)
            
        try:
            await db.commit()
            return True
        except Exception:
            await db.rollback()
            return False

    @staticmethod
    async def release_lock(db: AsyncSession, provider_name: str, worker_id: str) -> None:
        stmt = select(ProviderLock).where(
            ProviderLock.provider_name == provider_name,
            ProviderLock.locked_by == worker_id
        ).with_for_update()
        res = await db.execute(stmt)
        lock = res.scalar_one_or_none()
        if lock:
            await db.delete(lock)
            try:
                await db.commit()
            except Exception:
                await db.rollback()


class DeadLetterQueueService:
    @staticmethod
    async def add_failed_job(
        db: AsyncSession, provider_name: str, payload: dict, error_message: str, retry_count: int
    ) -> FailedSyncJob:
        dlq_job = FailedSyncJob(
            provider_name=provider_name,
            payload=payload,
            error_message=error_message,
            retry_count=retry_count
        )
        db.add(dlq_job)
        await db.commit()
        await db.refresh(dlq_job)
        return dlq_job


class SyncScheduler:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def sync_provider(self, provider_name: str, max_retries: int | None = None) -> dict:
        """
        Coordinates synchronization of a specific provider.
        Enforces rate-limits, health states, audits attempts, and handles retries.
        """
        name_clean = provider_name.lower().strip()

        # Get or create provider configuration
        config = await ProviderConfig.get_or_create(self.db, name_clean)

        # 1. Check if provider is enabled in registry and config
        if not config.enabled or not ProviderRegistry.is_enabled(name_clean):
            audit_log = await SyncAudit.create_log(self.db, name_clean)
            await SyncAudit.complete_log(
                db=self.db,
                log_id=audit_log.id,
                jobs_received=0,
                jobs_created=0,
                jobs_updated=0,
                jobs_expired=0,
                status="disabled",
                error_message=f"Provider {provider_name} is manually disabled."
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Provider {provider_name} is currently disabled."
            )

        # 2. Check health status
        health = await ProviderHealthService.get_health(self.db, name_clean)
        if health["status"] == "unavailable":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Provider {provider_name} is unavailable due to repeated failures."
            )

        # 3. Check Rate Limiting (passing db session)
        if not await ProviderRateLimiter.check_rate_limit(name_clean, self.db):
            retry_after = await ProviderRateLimiter.get_retry_after(name_clean, self.db)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded for provider {provider_name}. Retry after {int(retry_after)}s.",
                headers={"Retry-After": str(int(retry_after))}
            )

        # 4. Acquire distributed lock
        worker_id = f"worker-{uuid.uuid4()}"
        locked = await ProviderLockService.acquire_lock(self.db, name_clean, config.timeout_seconds, worker_id)
        if not locked:
            logger.warning(f"Sync skipped: provider {provider_name} is locked by another worker.")
            audit_log = await SyncAudit.create_log(self.db, name_clean)
            await SyncAudit.complete_log(
                db=self.db,
                log_id=audit_log.id,
                jobs_received=0,
                jobs_created=0,
                jobs_updated=0,
                jobs_expired=0,
                status="locked",
                error_message=f"Sync skipped: provider {provider_name} is locked by another worker."
            )
            return {
                "status": "locked",
                "message": f"Sync skipped: provider {provider_name} is locked by another worker.",
                "processed_count": 0,
                "new_count": 0,
                "updated_count": 0,
                "duration_seconds": 0.0
            }

        # 5. Sync execution loop (supporting retry mechanism)
        attempts = 0
        ingestion_service = JobIngestionService(self.db)
        retry_limit = max_retries if max_retries is not None else config.retry_limit
        
        try:
            while True:
                # Create a running audit log record
                audit_log = await SyncAudit.create_log(self.db, name_clean)
                start_time = datetime.now(timezone.utc)
                try:
                    # Execute ingestion
                    res = await ingestion_service.ingest_jobs(name_clean)

                    # Record success to rate limiter and complete log
                    ProviderRateLimiter.record_success(name_clean)
                    dur_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
                    await SyncAudit.complete_log(
                        db=self.db,
                        log_id=audit_log.id,
                        jobs_received=res["processed_count"],
                        jobs_created=res["new_count"],
                        jobs_updated=res["updated_count"],
                        jobs_expired=0,
                        status="success",
                        records_processed=res["processed_count"],
                        execution_duration_ms=dur_ms,
                        retry_count=attempts
                    )
                    return res

                except Exception as e:
                    attempts += 1
                    logger.error(
                        f"Sync attempt {attempts} failed for provider {provider_name}: {str(e)}", 
                        exc_info=True
                    )
                    
                    # Record failure to apply backoff cooldown
                    ProviderRateLimiter.record_failure(name_clean)
                    
                    # Complete the current log record with failed status (or retrying status)
                    dur_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
                    log_status = "retrying" if attempts <= retry_limit else "failed"
                    await SyncAudit.complete_log(
                        db=self.db,
                        log_id=audit_log.id,
                        jobs_received=0,
                        jobs_created=0,
                        jobs_updated=0,
                        jobs_expired=0,
                        status=log_status,
                        error_message=str(e),
                        records_processed=0,
                        execution_duration_ms=dur_ms,
                        retry_count=attempts - 1
                    )

                    if attempts > retry_limit:
                        # Move failed sync details to the DLQ (Dead Letter Queue)
                        await DeadLetterQueueService.add_failed_job(
                            db=self.db,
                            provider_name=name_clean,
                            payload={
                                "error": str(e),
                                "attempts": attempts,
                                "failed_at": datetime.now(timezone.utc).isoformat()
                            },
                            error_message=str(e),
                            retry_count=attempts
                        )
                        # Propagate exception/HTTP error if all retries exhausted
                        raise HTTPException(
                            status_code=status.HTTP_502_BAD_GATEWAY,
                            detail=f"Synchronization failed for provider {provider_name} after {attempts} attempts. Error: {str(e)}"
                        )

                    # Wait for rate limiter cooldown before retrying
                    retry_wait = await ProviderRateLimiter.get_retry_after(name_clean, self.db)
                    logger.warning(f"Retrying provider {provider_name} sync in {retry_wait} seconds...")
                    await asyncio.sleep(retry_wait)
        finally:
            # Release lock in finally block
            await ProviderLockService.release_lock(self.db, name_clean, worker_id)

    async def sync_all(self) -> dict:
        """
        Sync all enabled providers globally.
        """
        providers = ProviderRegistry.list_providers()
        synced_count = 0
        failed_count = 0
        processed = 0
        created = 0
        updated = 0

        for prov in providers:
            # Verify database config is enabled too
            config = await ProviderConfig.get_or_create(self.db, prov["name"])
            if prov["enabled"] and config.enabled:
                try:
                    res = await self.sync_provider(prov["name"])
                    if res.get("status") != "locked":
                        processed += res.get("processed_count", 0)
                        created += res.get("new_count", 0)
                        updated += res.get("updated_count", 0)
                        synced_count += 1
                except Exception as e:
                    logger.error(f"Global sync error on provider {prov['name']}: {str(e)}")
                    failed_count += 1

        return {
            "status": "success",
            "synced_providers": synced_count,
            "failed_providers": failed_count,
            "processed_count": processed,
            "new_count": created,
            "updated_count": updated
        }

    async def refresh_expired_jobs(self) -> dict:
        """
        Runs job expiration logic and registers log event.
        """
        ingestion_service = JobIngestionService(self.db)
        res = await ingestion_service.mark_expired_jobs()
        return {
            "status": "success",
            "expired_jobs": res["expired_count"]
        }

