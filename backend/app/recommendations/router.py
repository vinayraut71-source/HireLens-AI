"""Recommendations & Feedback module — API router. Sprint 10."""
from typing import Annotated
import uuid
from fastapi import APIRouter, Depends

from datetime import datetime, timezone
from app.core.dependencies import DBSession, get_current_active_user
from app.users.models import User
from app.recommendations.schemas import (
    RecommendationSignalResponse,
    SignalGenerationSummary,
    FeedbackSummaryResponse,
    JobDiscoveryResponse,
    JobRecommendationResponse,
    RecommendationStatusUpdate,
)
from app.recommendations.service import FeedbackService, JobDiscoveryService

router = APIRouter(prefix="/feedback", tags=["Feedback Learning Loop"])


@router.post(
    "/generate",
    response_model=SignalGenerationSummary,
    summary="Trigger feedback signal generation",
    description="Analyzes application outcomes and roadmap milestones to generate recommendation signals.",
)
async def generate_feedback_signals(
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    service = FeedbackService(db)
    return await service.generate_signals(current_user.id)


@router.get(
    "/signals",
    response_model=list[RecommendationSignalResponse],
    summary="Get recommendation signals",
    description="Returns list of generated recommendation signals for the user.",
)
async def get_recommendation_signals(
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    service = FeedbackService(db)
    return await service.get_signals(current_user.id)


@router.get(
    "/summary",
    response_model=FeedbackSummaryResponse,
    summary="Get feedback learning summary",
    description="Aggregates recommendation signals to provide a summary of successful skills and resume conversion rates.",
)
async def get_feedback_summary(
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    service = FeedbackService(db)
    return await service.get_summary(current_user.id)


discovery_router = APIRouter(prefix="/recommendations", tags=["Job Recommendations"])


@discovery_router.post(
    "/generate",
    response_model=JobDiscoveryResponse,
    summary="Explicitly generate job recommendations",
)
async def generate_recommendations(
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    service = JobDiscoveryService(db)
    recs = await service.discover_jobs(current_user.id)
    return {
        "recommendations": recs,
        "total_recommendations": len(recs),
        "generated_at": datetime.now(timezone.utc)
    }


@discovery_router.get(
    "",
    response_model=JobDiscoveryResponse,
    summary="Get job recommendations (uses cache)",
)
async def get_recommendations(
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    service = JobDiscoveryService(db)
    recs = await service.get_recommendations(current_user.id)
    return {
        "recommendations": recs,
        "total_recommendations": len(recs),
        "generated_at": datetime.now(timezone.utc)
    }


@discovery_router.get(
    "/saved",
    response_model=JobDiscoveryResponse,
    summary="Get saved job recommendations",
)
async def get_saved_recommendations(
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    service = JobDiscoveryService(db)
    recs = await service.get_saved_recommendations(current_user.id)
    return {
        "recommendations": recs,
        "total_recommendations": len(recs),
        "generated_at": datetime.now(timezone.utc)
    }


@discovery_router.post(
    "/refresh",

    response_model=JobDiscoveryResponse,
    summary="Refresh/recalculate job recommendations",
)
async def refresh_recommendations(
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    service = JobDiscoveryService(db)
    recs = await service.refresh_recommendations(current_user.id)
    return {
        "recommendations": recs,
        "total_recommendations": len(recs),
        "generated_at": datetime.now(timezone.utc)
    }


@discovery_router.patch(
    "/{recommendation_id}/status",
    response_model=JobRecommendationResponse,
    summary="Update recommendation status",
)
async def update_recommendation_status(
    recommendation_id: uuid.UUID,
    body: RecommendationStatusUpdate,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    service = JobDiscoveryService(db)
    return await service.update_recommendation_status(
        recommendation_id=recommendation_id,
        user_id=current_user.id,
        status=body.status
    )


