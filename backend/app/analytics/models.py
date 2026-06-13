"""
Analytics module — models.
PRD Section 7.2: user_analytics_snapshots.
"""
import uuid
from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
