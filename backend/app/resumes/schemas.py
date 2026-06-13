"""Resumes module — Pydantic schemas. PRD Section 8.4."""
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

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


