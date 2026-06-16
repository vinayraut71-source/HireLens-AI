"""Resumes module — API router. PRD Section 8.4: Resume Profile & Version Endpoints."""
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, UploadFile, File, status, HTTPException

from app.core.dependencies import DBSession, get_current_active_user
from app.users.models import User
from app.resumes.schemas import (
    ResumeProfileResponse,
    ResumeVersionResponse,
    ActivateVersionRequest,
    ResumeParsedResponse,
    AtsScoreRequest,
    ATSAnalysisResponse,
    ResumeTailoringRequest,
    ResumeTailoringResponse,
    ResumeTailoringSessionResponse,
)
from app.resumes.service import ResumeStorageService, ResumeVersionService, ResumeTailoringService

router = APIRouter(prefix="/resumes", tags=["Resumes"])


@router.post(
    "/upload",
    response_model=ResumeVersionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a new resume version",
    description="Upload a PDF or DOCX resume. Creates a profile if this is the first upload, otherwise appends a new version."
)
async def upload_resume(
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)],
    file: UploadFile = File(...)
):
    # 1. Validate file extension
    filename = file.filename
    if not filename:
        raise HTTPException(status_code=400, detail="Filename cannot be empty")
    ext = filename.split(".")[-1].lower()
    if ext not in ["pdf", "docx"]:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are allowed.")
    
    # 2. Read file data and validate size
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds the 5 MB limit.")
    
    # 3. Call service layer
    storage_service = ResumeStorageService()
    version_service = ResumeVersionService(db, storage_service)
    
    mime_type = file.content_type or ("application/pdf" if ext == "pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    
    version = await version_service.upload_resume(
        user_id=current_user.id,
        filename=filename,
        file_content=content,
        mime_type=mime_type
    )
    return version


@router.get(
    "",
    response_model=list[ResumeProfileResponse],
    summary="List resume profiles",
    description="Lists all active resume profiles belonging to the authenticated user."
)
async def list_profiles(
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    version_service = ResumeVersionService(db, ResumeStorageService())
    return await version_service.list_profiles(current_user.id)


@router.get(
    "/{profile_id}",
    response_model=ResumeProfileResponse,
    summary="Get resume profile detail",
    description="Returns detailed info for a specific resume profile owned by the authenticated user."
)
async def get_profile(
    profile_id: UUID,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    version_service = ResumeVersionService(db, ResumeStorageService())
    profile = await version_service.get_profile(current_user.id, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Resume profile not found")
    return profile


@router.get(
    "/{profile_id}/versions",
    response_model=list[ResumeVersionResponse],
    summary="List all versions for a profile",
    description="Lists all versions for a specific resume profile owned by the authenticated user."
)
async def list_versions(
    profile_id: UUID,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    version_service = ResumeVersionService(db, ResumeStorageService())
    # Verify profile exists
    profile = await version_service.get_profile(current_user.id, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Resume profile not found")
    
    return await version_service.list_versions(current_user.id, profile_id)


@router.post(
    "/{profile_id}/activate-version",
    response_model=ResumeProfileResponse,
    summary="Set active resume version",
    description="Sets the active version of a resume profile to the requested version ID."
)
async def activate_version(
    profile_id: UUID,
    body: ActivateVersionRequest,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    version_service = ResumeVersionService(db, ResumeStorageService())
    return await version_service.activate_version(
        user_id=current_user.id,
        profile_id=profile_id,
        version_id=body.version_id
    )


@router.post(
    "/{version_id}/parse",
    response_model=ResumeVersionResponse,
    summary="Parse a resume version",
    description="Deterministic parsing of a resume version from MinIO, extracting raw text and structured fields."
)
async def parse_version(
    version_id: UUID,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    version_service = ResumeVersionService(db, ResumeStorageService())
    return await version_service.parse_version(current_user.id, version_id)


@router.get(
    "/{version_id}/parsed",
    response_model=ResumeParsedResponse,
    summary="Get parsed resume fields",
    description="Retrieves the structured parsed data (contact info, education, experience, skills, certifications) for a version."
)
async def get_parsed_data(
    version_id: UUID,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    version_service = ResumeVersionService(db, ResumeStorageService())
    return await version_service.get_parsed_data(current_user.id, version_id)


@router.post(
    "/{version_id}/ats-score",
    response_model=ATSAnalysisResponse,
    summary="Compute ATS score against a job description",
    description="Deterministic rules-based scoring of a resume version against the provided job description text."
)
async def compute_ats_score(
    version_id: UUID,
    body: AtsScoreRequest,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    version_service = ResumeVersionService(db, ResumeStorageService())
    return await version_service.analyze_ats(
        user_id=current_user.id,
        version_id=version_id,
        job_description=body.job_description
    )


@router.get(
    "/{version_id}/ats-history",
    response_model=list[ATSAnalysisResponse],
    summary="Retrieve ATS analysis history",
    description="Lists all historical ATS analysis results for this resume version, sorted by creation date."
)
async def get_ats_history(
    version_id: UUID,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    version_service = ResumeVersionService(db, ResumeStorageService())
    return await version_service.list_ats_history(current_user.id, version_id)


@router.post(
    "/{version_id}/tailor",
    response_model=ResumeTailoringResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate tailored resume recommendations",
    description="Analyzes the resume version against a job description and provides tailored suggestions."
)
async def tailor_resume(
    version_id: UUID,
    body: ResumeTailoringRequest,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)],
    mode: str = "deterministic"
):
    if mode not in ["deterministic", "ai_assisted"]:
        raise HTTPException(status_code=400, detail="Invalid tailoring mode. Must be 'deterministic' or 'ai_assisted'.")
    
    return await ResumeTailoringService.tailor_resume(
        db=db,
        user_id=current_user.id,
        version_id=version_id,
        job_description=body.job_description,
        job_title=body.job_title,
        company_name=body.company_name,
        mode=mode
    )


@router.get(
    "/tailoring/{session_id}",
    response_model=ResumeTailoringSessionResponse,
    summary="Retrieve tailoring session",
    description="Retrieves the details and recommendations of a specific resume tailoring session."
)
async def get_tailoring_session(
    session_id: UUID,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    session = await ResumeTailoringService.get_tailoring_session(db, current_user.id, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Resume tailoring session not found.")
    return session


@router.get(
    "/{version_id}/tailoring-history",
    response_model=list[ResumeTailoringSessionResponse],
    summary="Retrieve history",
    description="Lists all historical tailoring sessions for a specific resume version."
)
async def get_tailoring_history(
    version_id: UUID,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return await ResumeTailoringService.get_tailoring_history(db, current_user.id, version_id)


@router.delete(
    "/tailoring/{session_id}",
    summary="Delete tailoring session",
    description="Deletes a specific resume tailoring session and its cascade recommendations."
)
async def delete_tailoring_session(
    session_id: UUID,
    db: DBSession,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    deleted = await ResumeTailoringService.delete_tailoring_session(db, current_user.id, session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Resume tailoring session not found.")
    return {"status": "success", "message": "Tailoring session deleted successfully."}




