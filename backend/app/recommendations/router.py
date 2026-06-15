"""Recommendations & Feedback module — API router. Sprint 10."""
from typing import Annotated
from fastapi import APIRouter, Depends

from app.core.dependencies import DBSession, get_current_active_user
from app.users.models import User
from app.recommendations.schemas import (
    RecommendationSignalResponse,
    SignalGenerationSummary,
    FeedbackSummaryResponse,
)
from app.recommendations.service import FeedbackService

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
