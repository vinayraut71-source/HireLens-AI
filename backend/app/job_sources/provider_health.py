"""
Provider Health Service — tracks failure rates and sync performance of providers.
Sprint 13: Framework.
"""
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.job_sources.models import ProviderSyncLog
from app.job_sources.providers import PROVIDER_REGISTRY


class ProviderHealthService:
    @staticmethod
    async def get_health(db: AsyncSession, provider_name: str) -> dict:
        """
        Computes the health metrics and status of a single provider by checking sync history.
        """
        from app.job_sources.provider_registry import ProviderRegistry
        from app.job_sources.models import ProviderConfig
        config = await ProviderConfig.get_or_create(db, provider_name)
        is_disabled = not config.enabled or not ProviderRegistry.is_enabled(provider_name)

        # Fetch up to 10 latest sync logs for this provider
        stmt = (
            select(ProviderSyncLog)
            .where(ProviderSyncLog.provider_name == provider_name)
            .order_by(ProviderSyncLog.sync_started_at.desc())
            .limit(10)
        )
        res = await db.execute(stmt)
        logs = list(res.scalars().all())

        if not logs:
            return {
                "provider_name": provider_name,
                "status": "disabled" if is_disabled else "healthy",
                "last_successful_sync": None,
                "failure_count": 0,
                "success_rate": 1.0,
                "avg_duration_seconds": 0.0
            }

        total_runs = len(logs)
        failed_runs = sum(1 for log in logs if log.status == "failed")
        success_rate = (total_runs - failed_runs) / total_runs

        # Calculate consecutive failures (from latest downwards)
        consecutive_failures = 0
        for log in logs:
            if log.status == "failed":
                consecutive_failures += 1
            else:
                break

        # Calculate average sync duration using execution_duration_ms if available, falling back to timestamps
        durations = []
        last_successful = None
        for log in logs:
            if log.status == "success" and not last_successful:
                last_successful = log.sync_completed_at
            if getattr(log, "execution_duration_ms", 0) > 0:
                durations.append(log.execution_duration_ms / 1000.0)
            elif log.sync_completed_at and log.sync_started_at:
                dur = (log.sync_completed_at - log.sync_started_at).total_seconds()
                durations.append(dur)

        avg_duration = sum(durations) / len(durations) if durations else 0.0

        # Classify Health State
        if is_disabled:
            status = "disabled"
        elif consecutive_failures >= 3:
            status = "unavailable"
        elif success_rate < 0.8:
            status = "degraded"
        elif success_rate <= 0.95:
            status = "warning"
        else:
            status = "healthy"

        return {
            "provider_name": provider_name,
            "status": status,
            "last_successful_sync": last_successful,
            "failure_count": failed_runs,
            "success_rate": success_rate,
            "avg_duration_seconds": round(avg_duration, 3)
        }

    @classmethod
    async def get_all_health(cls, db: AsyncSession) -> list[dict]:
        """
        Get the health state of all registered providers.
        """
        healths = []
        for name in PROVIDER_REGISTRY.keys():
            h = await cls.get_health(db, name)
            healths.append(h)
        return healths
