"""Jobs module — schemas. PRD Section 8.5."""
from uuid import UUID
from pydantic import BaseModel

class JobCreateRequest(BaseModel): title: str; description: str; company: str | None = None; source_url: str | None = None; location: str | None = None; remote_type: str | None = None; salary_min: int | None = None; salary_max: int | None = None
class JobResponse(BaseModel):
    id: UUID; title: str; company: str | None; description: str; is_saved: bool
    class Config: from_attributes = True
class JobUpdateRequest(BaseModel): notes: str | None = None; is_saved: bool | None = None
class MatchRequest(BaseModel): version_id: UUID
class MatchResponse(BaseModel): match_result_id: UUID; overall_score: float; ats_score: int | None = None; matched_skills: list = []; partial_skills: list = []; missing_skills: list = []; ai_analysis: str | None = None
class SkillGapResponse(BaseModel):
    id: UUID; skill_name: str; priority: str; category: str | None = None; status: str
    class Config: from_attributes = True
