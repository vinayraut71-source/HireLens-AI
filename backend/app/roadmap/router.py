"""Roadmap module — API router. PRD Section 8.6."""
from uuid import UUID
from fastapi import APIRouter
from app.core.dependencies import DBSession

router = APIRouter(prefix="/roadmaps", tags=["Personalized Learning Roadmaps"])

@router.post("", status_code=201, summary="Generate learning roadmap")
async def generate_roadmap(db: DBSession): raise NotImplementedError("Sprint 5")

@router.get("", summary="List user roadmaps")
async def list_roadmaps(db: DBSession): raise NotImplementedError("Sprint 5")

@router.get("/{roadmap_id}", summary="Get roadmap details with modules")
async def get_roadmap(roadmap_id: UUID, db: DBSession): raise NotImplementedError("Sprint 5")

@router.patch("/{roadmap_id}/modules/{module_id}", summary="Update module progress")
async def update_module_progress(roadmap_id: UUID, module_id: UUID, db: DBSession): raise NotImplementedError("Sprint 5")
