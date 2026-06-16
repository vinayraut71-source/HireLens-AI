"""
Sync Audit — utilities to manage provider sync transaction logs.
Sprint 13: Framework.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.job_sources.models import ProviderSyncLog


class SyncAudit:
    @staticmethod
    async def create_log(db: AsyncSession, provider_name: str) -> ProviderSyncLog:
        """
        Creates a new log entry at the beginning of a provider synchronization run.
        """
        log = ProviderSyncLog(
            provider_name=provider_name,
            sync_started_at=datetime.now(timezone.utc),
            status="running"
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return log

    @staticmethod
    async def complete_log(
        db: AsyncSession,
        log_id: uuid.UUID,
        jobs_received: int,
        jobs_created: int,
        jobs_updated: int,
        jobs_expired: int,
        status: str,
        error_message: str | None = None,
        records_processed: int | None = None,
        execution_duration_ms: int | None = None,
        retry_count: int = 0
    ) -> ProviderSyncLog:
        """
        Updates a sync log entry upon provider run completion (success or fail).
        """
        stmt = select(ProviderSyncLog).where(ProviderSyncLog.id == log_id)
        res = await db.execute(stmt)
        log = res.scalar_one_or_none()
        if log:
            log.sync_completed_at = datetime.now(timezone.utc)
            log.jobs_received = jobs_received
            log.jobs_created = jobs_created
            log.jobs_updated = jobs_updated
            log.jobs_expired = jobs_expired
            log.status = status
            log.error_message = error_message
            log.records_processed = records_processed if records_processed is not None else jobs_received
            if execution_duration_ms is not None:
                log.execution_duration_ms = execution_duration_ms
            else:
                started = log.sync_started_at.replace(tzinfo=None) if log.sync_started_at.tzinfo else log.sync_started_at
                completed = log.sync_completed_at.replace(tzinfo=None) if log.sync_completed_at.tzinfo else log.sync_completed_at
                dur = (completed - started).total_seconds()
                log.execution_duration_ms = int(dur * 1000)
            log.retry_count = retry_count
            log.updated_at = datetime.now(timezone.utc)
            await db.commit()
            await db.refresh(log)
        return log

    @staticmethod
    async def get_history(db: AsyncSession, limit: int = 50, offset: int = 0) -> list[ProviderSyncLog]:
        """
        Fetches historical logs ordered by started date descending.
        """
        stmt = (
            select(ProviderSyncLog)
            .order_by(desc(ProviderSyncLog.sync_started_at))
            .limit(limit)
            .offset(offset)
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())
