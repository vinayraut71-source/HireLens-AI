"""Users module — API router. PRD Section 8.3."""
from fastapi import APIRouter
from app.core.dependencies import DBSession

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", summary="Get user profile", description="Returns the authenticated user's profile and plan tier.")
async def get_profile(db: DBSession): raise NotImplementedError("Sprint 1")

@router.patch("/me", summary="Update user profile", description="Partial update of profile fields.")
async def update_profile(db: DBSession): raise NotImplementedError("Sprint 1")

@router.get("/me/preferences", summary="Get job preferences", description="Returns stored job search preferences.")
async def get_preferences(db: DBSession): raise NotImplementedError("Sprint 1")

@router.put("/me/preferences", summary="Update job preferences", description="Replace all preference fields.")
async def update_preferences(db: DBSession): raise NotImplementedError("Sprint 1")

@router.get("/me/dashboard", summary="Dashboard summary", description="Aggregated summary: ATS, applications, gaps, matches.")
async def get_dashboard(db: DBSession): raise NotImplementedError("Sprint 6")
