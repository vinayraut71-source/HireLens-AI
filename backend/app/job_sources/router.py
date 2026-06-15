"""
Job Sources API Router — handles ingestion trigger, refresh, stats, and source lists.
Sprint 12: Ingestion layer.
"""
from typing import Annotated
from fastapi import APIRouter, Depends
from datetime import datetime, timezone
from sqlalchemy import func, select

from app.core.dependencies import DBSession, get_current_active_user, get_current_admin_user
from app.users.models import User
from app.jobs.models import Job
from app.job_sources.models import ExternalJobSource
from app.job_sources.providers import PROVIDER_REGISTRY
from app.job_sources.schemas import (
    IngestionRequest,
    IngestionResponse,
    SourceStatsResponse,
    JobSourceResponse,
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
