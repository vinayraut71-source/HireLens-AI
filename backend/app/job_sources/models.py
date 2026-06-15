"""
External Job Sources module — models.
Sprint 12: Ingestion layer.
"""
import uuid
from datetime import datetime
from sqlalchemy import DateTime, Index, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base import BaseModel


class ExternalJobSource(BaseModel):
    __tablename__ = "external_job_sources"

    source_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source_job_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("source_name", "source_job_id", name="uq_external_job_sources_source_name_job_id"),
        Index("ix_external_job_sources_source_name_job_id", "source_name", "source_job_id"),
    )
