"""Jobs module — API router. PRD Section 8.5 + 8.6."""
from uuid import UUID
from fastapi import APIRouter
from app.core.dependencies import DBSession

router = APIRouter(prefix="/jobs", tags=["Jobs & Matching"])

@router.post("", status_code=201, summary="Create/save a job", description="Save a job from pasted JD text.")
async def create_job(db: DBSession): raise NotImplementedError("Sprint 4")
@router.get("", summary="List saved jobs")
async def list_jobs(db: DBSession): raise NotImplementedError("Sprint 4")
@router.get("/{job_id}", summary="Get job details")
async def get_job(job_id: UUID, db: DBSession): raise NotImplementedError("Sprint 4")
@router.patch("/{job_id}", summary="Update job notes/save status")
async def update_job(job_id: UUID, db: DBSession): raise NotImplementedError("Sprint 4")
@router.delete("/{job_id}", status_code=204, summary="Delete job")
async def delete_job(job_id: UUID, db: DBSession): raise NotImplementedError("Sprint 4")
@router.post("/{job_id}/match", summary="Match resume against job", description="Computes semantic match + skill gap analysis.")
async def match_resume(job_id: UUID, db: DBSession): raise NotImplementedError("Sprint 4")
@router.post("/analyze", summary="Analyze JD without saving", description="Quick JD analysis without persisting.")
async def analyze_jd(db: DBSession): raise NotImplementedError("Sprint 4")

# --- Skill Gap Endpoints (PRD 8.6) ---
@router.get("/skill-gaps", summary="List user skill gaps", tags=["Skill Gaps"])
async def list_skill_gaps(db: DBSession): raise NotImplementedError("Sprint 4")
@router.patch("/skill-gaps/{gap_id}", summary="Update gap status", tags=["Skill Gaps"])
async def update_skill_gap(gap_id: UUID, db: DBSession): raise NotImplementedError("Sprint 4")
