"""Infrastructure module — API router."""
from fastapi import APIRouter
from app.core.dependencies import DBSession

router = APIRouter(prefix="/infrastructure", tags=["Infrastructure & Admin"])

@router.get("/health", summary="Check infrastructure health status")
async def check_health(db: DBSession): raise NotImplementedError("Sprint 0")
