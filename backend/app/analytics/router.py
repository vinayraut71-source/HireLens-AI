"""Analytics module — API router. PRD Section 8.8."""
from fastapi import APIRouter
from app.core.dependencies import DBSession

router = APIRouter(prefix="/analytics", tags=["Analytics & Insights"])

@router.get("/summary", summary="Get application analytics summary", description="Returns current job tracking funnel rates and stats.")
async def get_summary(db: DBSession): raise NotImplementedError("Sprint 6")

@router.get("/timeseries", summary="Get metrics over time", description="Returns time-series dataset for rendering charts.")
async def get_timeseries(db: DBSession): raise NotImplementedError("Sprint 6")
