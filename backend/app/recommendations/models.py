"""
Recommendations module — models.
PRD Section 7.2: recommendation_signals.
"""
import uuid
from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base import BaseModel


class RecommendationSignal(BaseModel):
    """Sprint 10: Signals reflecting user preferences/outcomes for recommendation logic."""

    __tablename__ = "recommendation_signals"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    application_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_applications.id", ondelete="SET NULL"), nullable=True, index=True
    )
    resume_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resume_versions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    job_match_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_matches.id", ondelete="SET NULL"), nullable=True, index=True
    )
    signal_type: Mapped[str] = mapped_column(String(50), nullable=False)
    signal_source: Mapped[str] = mapped_column(String(50), nullable=False)
    signal_value: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    signal_weight: Mapped[float] = mapped_column(Float, nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, server_default="{}")
