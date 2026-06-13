"""Users module — Pydantic schemas. PRD Section 8.3."""
from typing import Any
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field

class UserResponse(BaseModel):
    id: UUID; email: str; full_name: str; avatar_url: str | None = None
    plan_tier: str; is_active: bool; is_verified: bool
    class Config: from_attributes = True

class UserUpdateRequest(BaseModel):
    full_name: str | None = None; avatar_url: str | None = None

class PreferenceResponse(BaseModel):
    id: UUID; target_role: str | None = None; target_industry: str | None = None
    preferred_locations: list = []; remote_preference: str = "any"
    min_salary: int | None = None; max_salary: int | None = None
    experience_years: int | None = None
    class Config: from_attributes = True

class PreferenceUpdateRequest(BaseModel):
    target_role: str | None = None; target_industry: str | None = None
    preferred_locations: list | None = None; remote_preference: str | None = None
    min_salary: int | None = None; max_salary: int | None = None
    experience_years: int | None = None

class DashboardResponse(BaseModel):
    default_resume: dict | None = None; applications: dict | None = None
    top_skill_gaps: list = []; recent_matches: list = []
    analytics_summary: dict | None = None
