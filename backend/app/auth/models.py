"""
Auth module — models.

No dedicated auth table; auth operates on the users table.
Refresh tokens are stored hashed in a dedicated table.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base import BaseModel


class RefreshToken(BaseModel):
    """
    Hashed refresh tokens — PRD Section 10.1.
    
    Security & Audit Design:
    - Token Rotation: On every refresh request, the current token is invalidated/revoked,
      and a new one is issued (Token Rotation) to prevent replay attacks.
    - Token Revocation: Tokens can be explicitly marked as revoked (e.g. on logout).
      Both `is_revoked` status and `revoked_at` timestamp are stored for auditing purposes.
    - Future Device Management: Nullable device information fields (device_name, user_agent, ip_address)
      are added to allow users to audit and revoke specific active sessions/devices in future sprints.
    """

    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    is_revoked: Mapped[bool] = mapped_column(default=False)
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Future Device Management fields
    device_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
