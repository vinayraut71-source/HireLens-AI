"""
Recommendations module — models.
PRD Section 7.2: recommendation_signals.
"""
import uuid

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base import BaseModel


class RecommendationSignal(BaseModel):
    """Signals reflecting user preferences for training recommendation engine. PRD Section 7.2."""

    __tablename__ = "recommendation_signals"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    signal_type: Mapped[str] = mapped_column(String(30), nullable=False)  # job / skill / resume_suggestion
    signal_key: Mapped[str] = mapped_column(String(255), nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    sample_count: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
