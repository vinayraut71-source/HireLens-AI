"""
Analytics module — models.
PRD Section 7.2: user_analytics_snapshots, analytics_snapshots, analytics_insights.
"""
import uuid
from datetime import date, datetime

from sqlalchemy import Date, Float, ForeignKey, Integer, UniqueConstraint, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.shared.base import BaseModel


class UserAnalyticsSnapshot(BaseModel):
    """Aggregated daily/weekly analytics for a user. PRD Section 7.2."""

    __tablename__ = "user_analytics_snapshots"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_applications: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    applications_this_month: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    interview_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    rejection_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    offer_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_match_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_ats_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    ats_improvement: Mapped[int | None] = mapped_column(Integer, nullable=True)
    skills_completed: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    __table_args__ = (
        UniqueConstraint("user_id", "snapshot_date", name="uq_user_analytics_snapshots_user_date"),
    )


class AnalyticsSnapshot(BaseModel):
    """Sprint 9: Analytics Snapshot recording aggregated metrics for dashboard."""

    __tablename__ = "analytics_snapshots"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    total_applications: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    total_interviews: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    total_offers: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    total_rejections: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    total_acceptances: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)

    response_rate: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0", nullable=False)
    interview_rate: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0", nullable=False)
    offer_rate: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0", nullable=False)
    acceptance_rate: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0", nullable=False)

    average_ats_score: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0", nullable=False)
    average_match_score: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0", nullable=False)

    # Deltas (comparing current vs previous snapshot)
    ats_score_delta: Mapped[float | None] = mapped_column(Float, nullable=True)
    match_score_delta: Mapped[float | None] = mapped_column(Float, nullable=True)
    application_rate_delta: Mapped[float | None] = mapped_column(Float, nullable=True)
    interview_rate_delta: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Funnel Counts
    funnel_stage_counts: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    strongest_resume_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resume_versions.id", ondelete="SET NULL"), nullable=True
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), server_default=func.now(), nullable=False
    )

    # Relationships
    insights: Mapped[list["AnalyticsInsight"]] = relationship(
        back_populates="snapshot", cascade="all, delete-orphan", passive_deletes=True
    )


class AnalyticsInsight(BaseModel):
    """Sprint 9: Analytics Insight recording deterministic insights."""

    __tablename__ = "analytics_insights"

    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analytics_snapshots.id", ondelete="CASCADE"), nullable=False, index=True
    )
    insight_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    impact_score: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationship
    snapshot: Mapped["AnalyticsSnapshot"] = relationship(back_populates="insights")

