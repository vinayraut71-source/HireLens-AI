import uuid
from datetime import datetime
from sqlalchemy import Float, String, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.base import Base

class CandidateMatch(Base):
    __tablename__ = "candidate_matches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_posting_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("job_postings.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    version_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("resume_versions.id", ondelete="CASCADE"), nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    matched_skills: Mapped[dict] = mapped_column(JSONB, default=list, server_default='[]')
    missing_skills: Mapped[dict] = mapped_column(JSONB, default=list, server_default='[]')
    ai_summary: Mapped[str] = mapped_column(Text, nullable=True)
    recruiter_status: Mapped[str] = mapped_column(String(20), default="new") # new / shortlisted / rejected / contacted
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    job_posting = relationship("JobPosting")
    user = relationship("User")
    resume_version = relationship("ResumeVersion")
