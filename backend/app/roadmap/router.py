"""Roadmap module — API router. PRD Section 8.6."""
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends

from app.core.dependencies import DBSession, get_current_active_user
from app.users.models import User
from app.roadmap.service import RoadmapService
from app.roadmap.schemas import MilestoneResponse, MilestonePatchRequest

router = APIRouter(prefix="/roadmaps", tags=["Personalized Learning Roadmaps"])

@router.post("", status_code=201, summary="Generate learning roadmap")
async def generate_roadmap(db: DBSession): raise NotImplementedError("Sprint 5")

@router.get("", summary="List user roadmaps")
async def list_roadmaps(db: DBSession): raise NotImplementedError("Sprint 5")

@router.get("/{roadmap_id}", summary="Get roadmap details with modules")
async def get_roadmap(roadmap_id: UUID, db: DBSession): raise NotImplementedError("Sprint 5")

@router.patch("/{roadmap_id}/modules/{module_id}", summary="Update module progress")
async def update_module_progress(roadmap_id: UUID, module_id: UUID, db: DBSession): raise NotImplementedError("Sprint 5")


# --- Career Roadmap Endpoints (Sprint 7) ---

@router.patch(
    "/{roadmap_id}/milestones/{milestone_id}",
    response_model=MilestoneResponse,
    summary="Update roadmap milestone progress",
    description="Updates a milestone's completion status. Enforces ownership.",
    tags=["Career Roadmaps"],
)
async def update_milestone_progress(
    roadmap_id: UUID,
    milestone_id: UUID,
    body: MilestonePatchRequest,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    service = RoadmapService(db)
    return await service.patch_milestone(
        current_user.id, roadmap_id, milestone_id, body.completion_status
    )
