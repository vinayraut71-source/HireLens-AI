"""Resumes module — Pydantic schemas. PRD Section 8.4."""
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

class ResumeProfileCreate(BaseModel):
    name: str

class ResumeProfileResponse(BaseModel):
    id: UUID
    name: str
    is_default: bool
    version_count: int
    active_version_id: UUID | None = None
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class ResumeVersionResponse(BaseModel):
    id: UUID
    profile_id: UUID
    version_number: int
    original_filename: str
    storage_path: str
    file_size: int
    mime_type: str
    upload_source: str
    created_at: datetime
    class Config:
        from_attributes = True

class ActivateVersionRequest(BaseModel):
    version_id: UUID


class ResumeParsedResponse(BaseModel):
    contact_info: dict
    education: list
    experience: list
    skills: list
    certifications: list


class AtsScoreRequest(BaseModel):
    job_description: str = Field(..., max_length=50000)


class ATSAnalysisResponse(BaseModel):
    id: UUID
    resume_version_id: UUID
    job_description_hash: str
    ats_score: int
    keyword_score: int
    skills_score: int
    experience_score: int
    education_score: int
    missing_keywords: list[str]
    matched_keywords: list[str]
    recommendations: list[str]
    matched_skills: list[str]
    missing_skills: list[str]
    resume_strengths: list[str]
    resume_weaknesses: list[str]
    matched_sections: list[str]
    created_at: datetime

    class Config:
        from_attributes = True


