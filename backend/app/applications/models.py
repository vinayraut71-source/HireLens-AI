"""Applications module — models. PRD Section 7.2."""
import uuid
from datetime import date, datetime
import enum
from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, func, Enum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.shared.base import BaseModel


class OutcomeType(str, enum.Enum):
    unknown = "unknown"
    no_response = "no_response"
    rejected = "rejected"
    interviewed = "interviewed"
    offered = "offered"
    accepted = "accepted"

class Application(BaseModel):
    __tablename__ = "applications"
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True, index=True)
    version_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("resume_versions.id", ondelete="SET NULL"), nullable=True, index=True)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="saved", server_default="saved")
    match_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    applied_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    follow_up_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    job_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

class ApplicationPackage(BaseModel):
    __tablename__ = "application_packages"
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="SET NULL"), nullable=True, index=True)
    tailored_version_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("resume_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    cover_letter: Mapped[str | None] = mapped_column(Text, nullable=True)
    match_score: Mapped[float] = mapped_column(Float, nullable=False)
    approval_status: Mapped[str] = mapped_column(String(20), default="pending_review", server_default="pending_review")
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class OutcomeEvent(BaseModel):
    __tablename__ = "outcome_events"
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    version_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("resume_versions.id", ondelete="SET NULL"), nullable=True, index=True)
    match_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, server_default="{}")


class JobApplication(BaseModel):
    """Sprint 8: Job Application record for tracking progress."""
    __tablename__ = "job_applications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resume_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resume_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(30), default="draft", server_default="draft", nullable=False
    )
    outcome_type: Mapped[OutcomeType] = mapped_column(
        Enum(OutcomeType, name="outcome_type_enum"), default=OutcomeType.unknown, server_default="unknown", nullable=False
    )
    job_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Analytics Fields
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    first_response_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    interview_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    offer_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    timeline_events: Mapped[list["ApplicationTimelineEvent"]] = relationship(
        back_populates="application", cascade="all, delete-orphan", order_by="ApplicationTimelineEvent.created_at"
    )


class ApplicationTimelineEvent(BaseModel):
    """Sprint 8: Timeline event recording status transitions."""
    __tablename__ = "application_timeline_events"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    previous_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    new_status: Mapped[str] = mapped_column(String(30), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationship
    application: Mapped["JobApplication"] = relationship(back_populates="timeline_events")
