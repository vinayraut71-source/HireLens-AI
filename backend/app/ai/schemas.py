"""AI Layer — Pydantic schemas. PRD Section 9.0."""
from uuid import UUID
from pydantic import BaseModel

class AgentRunResponse(BaseModel):
    id: UUID
    agent_name: str
    status: str
    class Config: from_attributes = True

class AgentParseRequest(BaseModel):
    file_url: str

class AgentParseResponse(BaseModel):
    parsed_data: dict
    ats_score: int
    ats_feedback: dict
