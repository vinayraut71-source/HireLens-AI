"""Analytics module — API router. PRD Section 8.8 + Sprint 9."""
from fastapi import APIRouter, Depends
from typing import Annotated

from app.core.dependencies import DBSession, get_current_active_user
from app.users.models import User
from app.analytics.schemas import (
    AnalyticsOverviewResponse,
    AnalyticsSnapshotResponse,
    AnalyticsInsightResponse,
)
from app.analytics.service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics & Insights"])


@router.post(
    "/generate",
    response_model=AnalyticsOverviewResponse,
    summary="Trigger analytics snapshot generation",
    description="Forces recalculation and generation of a new analytics snapshot and insights for the active user.",
)
async def generate_analytics(
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    service = AnalyticsService(db)
    await service.generate_snapshot(current_user.id)
    return await service.get_latest_overview(current_user.id)


@router.get(
    "",
    response_model=AnalyticsOverviewResponse,
    summary="Get latest analytics overview",
    description="Returns the most recent cached analytics snapshot and its insights. Generates one if it doesn't exist.",
)
async def get_analytics_overview(
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    service = AnalyticsService(db)
    return await service.get_latest_overview(current_user.id)


@router.get(
    "/history",
    response_model=list[AnalyticsSnapshotResponse],
    summary="Get analytics history",
    description="Returns a list of all historical analytics snapshots for the user, ordered by generation date descending.",
)
async def get_analytics_history(
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    service = AnalyticsService(db)
    return await service.get_history(current_user.id)


@router.get(
    "/insights",
    response_model=list[AnalyticsInsightResponse],
    summary="Get latest analytics insights",
    description="Returns the list of insights associated with the user's latest analytics snapshot.",
)
async def get_analytics_insights(
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    service = AnalyticsService(db)
    return await service.get_latest_insights(current_user.id)
