"""Jobs module — API router. PRD Section 8.5 + Sprint 5 Job Matching."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.dependencies import DBSession, get_current_active_user
from app.users.models import User
from app.jobs.schemas import (
    JobCreateRequest,
    JobResponse,
    JobUpdateRequest,
    JobMatchRequest,
    JobMatchResponse,
    JobMatchListResponse,
    SkillGapResponse,
    SkillGapSummaryResponse,
    SkillGapAnalysisResponse,
)
from app.jobs.service import JobService, JobMatchingService, SkillGapService
from app.roadmap.service import RoadmapService
from app.roadmap.schemas import CareerRoadmapResponse

router = APIRouter(prefix="/jobs", tags=["Jobs & Matching"])


# --- Job CRUD Endpoints ---

@router.post(
    "",
    response_model=JobResponse,
    status_code=201,
    summary="Create/save a job",
    description="Save a job from pasted JD text.",
)
async def create_job(
    body: JobCreateRequest,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    service = JobService(db)
    return await service.create_job(current_user.id, body.model_dump())


@router.get(
    "",
    response_model=list[JobResponse],
    summary="List saved jobs",
    description="Lists all saved (non-deleted) jobs for the authenticated user.",
)
async def list_jobs(
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    service = JobService(db)
    return await service.list_jobs(current_user.id)


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    summary="Get job details",
    description="Returns details for a specific job owned by the authenticated user.",
)
async def get_job(
    job_id: UUID,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    service = JobService(db)
    return await service.get_job(current_user.id, job_id)


@router.patch(
    "/{job_id}",
    response_model=JobResponse,
    summary="Update job notes/save status",
    description="Partial update on a job owned by the authenticated user.",
)
async def update_job(
    job_id: UUID,
    body: JobUpdateRequest,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    service = JobService(db)
    return await service.update_job(current_user.id, job_id, body.model_dump(exclude_unset=True))


@router.delete(
    "/{job_id}",
    status_code=204,
    summary="Delete job",
    description="Soft-deletes a job owned by the authenticated user.",
)
async def delete_job(
    job_id: UUID,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    service = JobService(db)
    await service.delete_job(current_user.id, job_id)


# --- Job Match Endpoints (Sprint 5) ---

@router.post(
    "/{job_id}/match",
    response_model=JobMatchResponse,
    status_code=201,
    summary="Match resume against job",
    description="Computes a deterministic match score between a resume version and a saved job description.",
)
async def match_resume(
    job_id: UUID,
    body: JobMatchRequest,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    service = JobMatchingService(db)
    return await service.match(current_user.id, job_id, body.resume_version_id)


@router.get(
    "/matches/list",
    response_model=list[JobMatchListResponse],
    summary="List all match results",
    description="Lists all job match results for the authenticated user, newest first.",
)
async def list_matches(
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    service = JobMatchingService(db)
    return await service.list_matches(current_user.id)


@router.get(
    "/matches/{match_id}",
    response_model=JobMatchResponse,
    summary="Get match details",
    description="Returns detailed match result for a specific match ID owned by the authenticated user.",
)
async def get_match(
    match_id: UUID,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    service = JobMatchingService(db)
    return await service.get_match(current_user.id, match_id)


# --- Skill Gap Endpoints (PRD 8.6 + Sprint 6) ---

@router.post(
    "/matches/{match_id}/skill-gap",
    response_model=SkillGapSummaryResponse,
    status_code=201,
    summary="Analyze skill gaps for a job match",
    description="Generates or retrieves the cached skill gap analysis for a specific job match.",
    tags=["Skill Gaps"],
)
async def analyze_skill_gaps(
    match_id: UUID,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    service = SkillGapService(db)
    gaps = await service.analyze_gaps(current_user.id, match_id)
    
    critical_count = sum(1 for g in gaps if g.learning_priority == "critical")
    high_count = sum(1 for g in gaps if g.learning_priority == "high")
    medium_count = sum(1 for g in gaps if g.learning_priority == "medium")
    low_count = sum(1 for g in gaps if g.learning_priority == "low")
    
    return SkillGapSummaryResponse(
        job_match_id=match_id,
        total_gaps=len(gaps),
        critical_count=critical_count,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,
        gaps=[SkillGapAnalysisResponse.model_validate(g) for g in gaps],
    )


@router.get(
    "/matches/{match_id}/skill-gap",
    response_model=SkillGapSummaryResponse,
    summary="Get skill gaps for a job match",
    description="Retrieves the cached skill gap analysis for a specific job match.",
    tags=["Skill Gaps"],
)
async def get_skill_gaps(
    match_id: UUID,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    service = SkillGapService(db)
    gaps = await service.get_gaps(current_user.id, match_id)
    
    critical_count = sum(1 for g in gaps if g.learning_priority == "critical")
    high_count = sum(1 for g in gaps if g.learning_priority == "high")
    medium_count = sum(1 for g in gaps if g.learning_priority == "medium")
    low_count = sum(1 for g in gaps if g.learning_priority == "low")
    
    return SkillGapSummaryResponse(
        job_match_id=match_id,
        total_gaps=len(gaps),
        critical_count=critical_count,
        high_count=high_count,
        medium_count=medium_count,
        low_count=low_count,
        gaps=[SkillGapAnalysisResponse.model_validate(g) for g in gaps],
    )


@router.get(
    "/skill-gaps",
    summary="List user skill gaps",
    tags=["Skill Gaps"],
)
async def list_skill_gaps(
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    raise NotImplementedError("Sprint 6")


@router.patch(
    "/skill-gaps/{gap_id}",
    summary="Update gap status",
    tags=["Skill Gaps"],
)
async def update_skill_gap(
    gap_id: UUID,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    raise NotImplementedError("Sprint 6")


# --- Career Roadmap Endpoints (Sprint 7) ---

@router.post(
    "/matches/{match_id}/roadmap",
    response_model=CareerRoadmapResponse,
    status_code=201,
    summary="Generate career roadmap for a job match",
    description="Generates a learning roadmap mapped from the skill gaps for a job match.",
    tags=["Career Roadmaps"],
)
async def generate_career_roadmap(
    match_id: UUID,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    service = RoadmapService(db)
    return await service.generate_roadmap(current_user.id, match_id)


@router.get(
    "/matches/{match_id}/roadmap",
    response_model=CareerRoadmapResponse,
    summary="Get career roadmap for a job match",
    description="Retrieves the cached learning roadmap for a specific job match.",
    tags=["Career Roadmaps"],
)
async def get_career_roadmap(
    match_id: UUID,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    service = RoadmapService(db)
    return await service.get_roadmap(current_user.id, match_id)
