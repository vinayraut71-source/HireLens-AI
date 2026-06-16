import uuid
from datetime import datetime
from sqlalchemy import DateTime, Index, String, Text, UniqueConstraint, func, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base import Base, TimestampMixin, BaseModel


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


class ProviderSyncLog(BaseModel):
    __tablename__ = "provider_sync_logs"

    provider_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    sync_started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, server_default=func.now(), index=True
    )
    sync_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    jobs_received: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    jobs_created: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    jobs_updated: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    jobs_expired: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # running, success, failed
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    records_processed: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    execution_duration_ms: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    retry_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class ProviderConfig(BaseModel):
    __tablename__ = "provider_configs"

    provider_name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    sync_interval_minutes: Mapped[int] = mapped_column(Integer, default=60, server_default="60", nullable=False)
    rate_limit_per_hour: Mapped[int] = mapped_column(Integer, default=10, server_default="10", nullable=False)
    retry_limit: Mapped[int] = mapped_column(Integer, default=3, server_default="3", nullable=False)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=30, server_default="30", nullable=False)
    max_concurrent_jobs: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)

    @classmethod
    async def get_or_create(cls, db, provider_name: str) -> "ProviderConfig":
        from sqlalchemy import select
        name_clean = provider_name.lower().strip()
        stmt = select(cls).where(cls.provider_name == name_clean)
        res = await db.execute(stmt)
        config = res.scalar_one_or_none()
        if not config:
            from app.job_sources.provider_registry import ProviderRegistry
            registry_enabled = ProviderRegistry.is_enabled(name_clean)
            config = cls(
                provider_name=name_clean,
                enabled=registry_enabled,
                sync_interval_minutes=60,
                rate_limit_per_hour=10,
                retry_limit=3,
                timeout_seconds=30,
                max_concurrent_jobs=1
            )
            db.add(config)
            await db.commit()
            await db.refresh(config)
        return config


class ProviderLock(Base, TimestampMixin):
    __tablename__ = "provider_locks"

    provider_name: Mapped[str] = mapped_column(String(50), primary_key=True)
    locked_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    locked_by: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, server_default=func.now(), nullable=False)


class FailedSyncJob(BaseModel):
    __tablename__ = "failed_sync_jobs"

    provider_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    payload: Mapped[dict] = mapped_column("payload", JSONB, default=dict, server_default="{}")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ProviderToggleAudit(BaseModel):
    __tablename__ = "provider_toggle_audits"

    admin_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    old_state: Mapped[bool] = mapped_column(Boolean, nullable=False)
    new_state: Mapped[bool] = mapped_column(Boolean, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, server_default=func.now(), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

