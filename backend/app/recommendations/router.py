"""Recommendations module — API router. PRD Section 8.5."""
from fastapi import APIRouter
from app.core.dependencies import DBSession

router = APIRouter(prefix="/recommendations", tags=["Recommendations & Discovery"])

@router.get("/jobs", summary="Get recommended jobs", description="Returns personalized list of job recommendations based on user vectors.")
async def get_recommended_jobs(db: DBSession): raise NotImplementedError("Sprint 4")
