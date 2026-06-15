"""Applications module — API router. Sprint 8 Application Tracking Engine."""
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends

from app.core.dependencies import DBSession, get_current_active_user
from app.users.models import User
from app.applications.schemas import (
    JobApplicationCreateRequest,
    JobApplicationResponse,
    JobApplicationStatusUpdateRequest,
    ApplicationTimelineEventResponse,
)
from app.applications.service import ApplicationTrackingService

router = APIRouter(prefix="/applications", tags=["Applications & Tracking"])


@router.post(
    "",
    response_model=JobApplicationResponse,
    status_code=201,
    summary="Track a new job application",
    description="Tracks an application for a specific job matching a resume version.",
)
async def create_job_application(
    body: JobApplicationCreateRequest,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    service = ApplicationTrackingService(db)
    return await service.create_application(current_user.id, body.model_dump())


@router.get(
    "",
    response_model=list[JobApplicationResponse],
    summary="List tracked applications",
    description="Returns list of all active applications for the user.",
)
async def list_job_applications(
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    service = ApplicationTrackingService(db)
    return await service.list_applications(current_user.id)


@router.get(
    "/{application_id}",
    response_model=JobApplicationResponse,
    summary="Get tracked application details",
    description="Returns detailed information of a tracked application. Enforces ownership.",
)
async def get_job_application(
    application_id: UUID,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    service = ApplicationTrackingService(db)
    return await service.get_application(current_user.id, application_id)


@router.patch(
    "/{application_id}/status",
    response_model=JobApplicationResponse,
    summary="Update application status",
    description="Updates the application status. Enforces transition flow and creates timeline events.",
)
async def update_job_application_status(
    application_id: UUID,
    body: JobApplicationStatusUpdateRequest,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    service = ApplicationTrackingService(db)
    return await service.update_status(
        user_id=current_user.id,
        application_id=application_id,
        new_status=body.status,
        notes=body.notes,
        outcome_type=body.outcome_type,
    )


@router.get(
    "/{application_id}/timeline",
    response_model=list[ApplicationTimelineEventResponse],
    summary="Get application progress timeline",
    description="Returns status transition timeline events for the application, ordered newest first.",
)
async def get_job_application_timeline(
    application_id: UUID,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    service = ApplicationTrackingService(db)
    return await service.get_timeline(current_user.id, application_id)
