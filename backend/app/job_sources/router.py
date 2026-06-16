"""
Job Sources API Router — handles ingestion trigger, refresh, stats, source lists, and provider sync framework.
Sprint 12 & 13.
"""
from typing import Annotated
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timezone
from sqlalchemy import func, select

from app.core.dependencies import DBSession, get_current_active_user, get_current_admin_user
from app.users.models import User
from app.jobs.models import Job
from app.job_sources.models import ExternalJobSource, ProviderConfig, ProviderToggleAudit, FailedSyncJob
from app.job_sources.providers import PROVIDER_REGISTRY
from app.job_sources.provider_registry import ProviderRegistry
from app.job_sources.provider_health import ProviderHealthService
from app.job_sources.rate_limiter import ProviderRateLimiter
from app.job_sources.sync_audit import SyncAudit
from app.job_sources.sync_scheduler import SyncScheduler
from app.job_sources.schemas import (
    IngestionRequest,
    IngestionResponse,
    SourceStatsResponse,
    JobSourceResponse,
    ProviderResponse,
    ProviderHealthSummary,
    SyncLogResponse,
    ProviderConfigUpdate,
    ProviderConfigResponse,
    FailedSyncJobResponse,
)
from app.job_sources.ingestion_service import JobIngestionService

router = APIRouter(prefix="/job-sources", tags=["Job Ingestion Layer"])


@router.post(
    "/ingest",
    response_model=IngestionResponse,
    summary="Trigger external job ingestion (Admin-only)",
    description="Collects new job postings from configured external job providers, normalizes and deduplicates them.",
)
async def ingest_jobs(
    body: IngestionRequest,
    db: DBSession,
    current_admin: Annotated[User, Depends(get_current_admin_user)],
):
    service = JobIngestionService(db)
    if body.source:
        return await service.ingest_jobs(body.source)
    else:
        return await service.ingest_all_sources()


@router.post(
    "/refresh",
    response_model=IngestionResponse,
    summary="Refresh/re-normalize active jobs (Admin-only)",
    description="Runs the normalization and hashing logic over all active external jobs in the database.",
)
async def refresh_jobs(
    db: DBSession,
    current_admin: Annotated[User, Depends(get_current_admin_user)],
):
    service = JobIngestionService(db)
    return await service.refresh_existing_jobs()


@router.get(
    "/stats",
    response_model=SourceStatsResponse,
    summary="Get ingestion dashboard statistics",
)
async def get_ingestion_stats(
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    # Total active/expired/archived
    total_res = await db.execute(select(func.count(Job.id)).where(Job.is_deleted == False))
    total = total_res.scalar() or 0

    active_res = await db.execute(select(func.count(Job.id)).where(Job.is_deleted == False, Job.job_status == "active"))
    active = active_res.scalar() or 0

    expired_res = await db.execute(select(func.count(Job.id)).where(Job.is_deleted == False, Job.job_status == "expired"))
    expired = expired_res.scalar() or 0

    archived_res = await db.execute(select(func.count(Job.id)).where(Job.is_deleted == False, Job.job_status == "archived"))
    archived = archived_res.scalar() or 0

    # Source metrics
    source_stmt = (
        select(Job.external_source, func.count(Job.id))
        .where(Job.is_deleted == False, Job.external_source.isnot(None))
        .group_by(Job.external_source)
    )
    source_res = await db.execute(source_stmt)
    sources_dict = {row[0]: row[1] for row in source_res.all()}

    return {
        "total_jobs": total,
        "active_jobs": active,
        "expired_jobs": expired,
        "archived_jobs": archived,
        "sources": sources_dict
    }


@router.get(
    "/sources",
    response_model=list[JobSourceResponse],
    summary="List all available job sources",
)
async def list_job_sources(
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    sources_list = []
    for name in PROVIDER_REGISTRY.keys():
        stmt = select(func.max(ExternalJobSource.last_seen_at)).where(
            ExternalJobSource.source_name == name
        )
        res = await db.execute(stmt)
        last_seen = res.scalar()
        sources_list.append({
            "name": name,
            "enabled": True,
            "last_ingested_at": last_seen
        })
    return sources_list


@router.post(
    "/sync",
    summary="Sync all enabled providers (Admin-only)",
    description="Syncs all enabled provider job postings sequentially.",
)
async def sync_all_providers(
    db: DBSession,
    current_admin: Annotated[User, Depends(get_current_admin_user)],
):
    scheduler = SyncScheduler(db)
    return await scheduler.sync_all()


@router.post(
    "/sync/{provider}",
    summary="Sync a specific provider (Admin-only)",
    description="Syncs job postings from a single enabled provider.",
)
async def sync_provider(
    provider: str,
    db: DBSession,
    current_admin: Annotated[User, Depends(get_current_admin_user)],
):
    scheduler = SyncScheduler(db)
    return await scheduler.sync_provider(provider)


@router.get(
    "/providers",
    response_model=list[ProviderResponse],
    summary="List all registered providers and their enabled states (Admin-only)",
)
async def list_providers(
    current_admin: Annotated[User, Depends(get_current_admin_user)],
):
    return ProviderRegistry.list_providers()


@router.patch(
    "/providers/{provider}/toggle",
    response_model=ProviderResponse,
    summary="Toggle provider enabled status (Admin-only)",
)
async def toggle_provider(
    provider: str,
    db: DBSession,
    current_admin: Annotated[User, Depends(get_current_admin_user)],
    reason: str | None = None,
):
    provider_clean = provider.lower().strip()
    if provider_clean not in PROVIDER_REGISTRY:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Provider {provider} not found."
        )

    config = await ProviderConfig.get_or_create(db, provider_clean)
    old_state = config.enabled
    new_state = not old_state

    # Save to config and toggle registry state
    config.enabled = new_state
    if new_state:
        ProviderRegistry.enable_provider(provider_clean)
    else:
        ProviderRegistry.disable_provider(provider_clean)

    # Store toggle audit log
    audit_log = ProviderToggleAudit(
        admin_user_id=current_admin.id,
        provider_name=provider_clean,
        old_state=old_state,
        new_state=new_state,
        timestamp=datetime.now(timezone.utc),
        reason=reason
    )
    db.add(audit_log)
    await db.commit()
        
    return {
        "name": provider_clean,
        "enabled": new_state
    }


@router.patch(
    "/providers/{provider}/config",
    response_model=ProviderConfigResponse,
    summary="Override provider configuration (Admin-only)",
)
async def override_provider_config(
    provider: str,
    body: ProviderConfigUpdate,
    db: DBSession,
    current_admin: Annotated[User, Depends(get_current_admin_user)],
):
    provider_clean = provider.lower().strip()
    if provider_clean not in PROVIDER_REGISTRY:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Provider {provider} not found."
        )

    config = await ProviderConfig.get_or_create(db, provider_clean)
    
    if body.enabled is not None:
        if config.enabled != body.enabled:
            if body.enabled:
                ProviderRegistry.enable_provider(provider_clean)
            else:
                ProviderRegistry.disable_provider(provider_clean)
        config.enabled = body.enabled

    if body.sync_interval_minutes is not None:
        config.sync_interval_minutes = body.sync_interval_minutes
    if body.rate_limit_per_hour is not None:
        config.rate_limit_per_hour = body.rate_limit_per_hour
    if body.retry_limit is not None:
        config.retry_limit = body.retry_limit
    if body.timeout_seconds is not None:
        config.timeout_seconds = body.timeout_seconds
    if body.max_concurrent_jobs is not None:
        config.max_concurrent_jobs = body.max_concurrent_jobs

    await db.commit()
    await db.refresh(config)
    return config


@router.get(
    "/health",
    response_model=list[ProviderHealthSummary],
    summary="Get health summaries of all providers (Admin-only)",
)
async def get_health_summaries(
    db: DBSession,
    current_admin: Annotated[User, Depends(get_current_admin_user)],
):
    return await ProviderHealthService.get_all_health(db)


@router.get(
    "/sync-history",
    response_model=list[SyncLogResponse],
    summary="Retrieve sync history logs (Admin-only)",
)
async def get_sync_history_history(
    db: DBSession,
    current_admin: Annotated[User, Depends(get_current_admin_user)],
    page: int = 1,
    page_size: int = 50,
):
    if page_size > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="page_size cannot exceed 100"
        )
    if page < 1 or page_size < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="page and page_size must be >= 1"
        )
    offset = (page - 1) * page_size
    return await SyncAudit.get_history(db, limit=page_size, offset=offset)


@router.get(
    "/failed-syncs",
    response_model=list[FailedSyncJobResponse],
    summary="List failed sync jobs (Admin-only)",
)
async def list_failed_sync_jobs(
    db: DBSession,
    current_admin: Annotated[User, Depends(get_current_admin_user)],
    page: int = 1,
    page_size: int = 50,
):
    if page_size > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="page_size cannot exceed 100"
        )
    offset = (page - 1) * page_size
    stmt = select(FailedSyncJob).order_by(FailedSyncJob.created_at.desc()).limit(page_size).offset(offset)
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.get(
    "/failed-syncs/{id}",
    response_model=FailedSyncJobResponse,
    summary="Get failed sync job details (Admin-only)",
)
async def get_failed_sync_job(
    id: uuid.UUID,
    db: DBSession,
    current_admin: Annotated[User, Depends(get_current_admin_user)],
):
    stmt = select(FailedSyncJob).where(FailedSyncJob.id == id)
    res = await db.execute(stmt)
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Failed sync job not found."
        )
    return job


@router.post(
    "/failed-syncs/{id}/replay",
    summary="Replay a failed sync job (Admin-only)",
)
async def replay_failed_sync_job(
    id: uuid.UUID,
    db: DBSession,
    current_admin: Annotated[User, Depends(get_current_admin_user)],
):
    stmt = select(FailedSyncJob).where(FailedSyncJob.id == id)
    res = await db.execute(stmt)
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Failed sync job not found."
        )

    # Replay execution
    scheduler = SyncScheduler(db)
    # Temporarily restore rate limiter settings for this provider if needed, or bypass rate limits
    # Wait, replaying should bypass the standard rate limits so it executes immediately!
    # Let's bypass it by resetting the rate limiter attempts/cooldown for this provider
    state = ProviderRateLimiter._get_state(job.provider_name)
    state["last_call_time"] = 0.0
    state["attempts"] = 0
    state["cooldown_until"] = 0.0
    
    sync_res = await scheduler.sync_provider(job.provider_name)

    # If successfully completed, mark DLQ job as resolved
    job.resolved = True
    job.resolved_at = datetime.now(timezone.utc)
    await db.commit()

    return {
        "status": "success",
        "replay_result": sync_res
    }

