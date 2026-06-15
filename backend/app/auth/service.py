"""
Auth module — service layer.
PRD Section 10.1: bcrypt cost 12, JWT access 15m + refresh 7d.
"""
from datetime import datetime, timedelta, timezone
import secrets
import logging
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status
from jose import JWTError

from app.core.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    hash_token,
    decode_token,
)
from app.users.models import User, UserPreference
from app.auth.models import RefreshToken, PasswordResetToken
from app.events.audit_events import UserAuthAuditEvent

logger = logging.getLogger("app.auth.service")


class AuthService:
    """Handles registration, login, token rotation, password reset."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, email: str, password: str, full_name: str) -> dict:
        """Create user with hashed password, return tokens."""
        email = email.strip().lower()
        # 1. Check if user already exists
        result = await self.db.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        try:
            # 2. Create user and empty user preference
            user = User(
                email=email,
                password_hash=hash_password(password),
                full_name=full_name,
            )
            self.db.add(user)
            await self.db.flush()

            preference = UserPreference(user_id=user.id)
            self.db.add(preference)

            # 3. Create tokens
            access_token = create_access_token(subject=user.id)
            refresh_token = create_refresh_token(subject=user.id)

            # 4. Save refresh token
            expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            # TODO: Track user_agent, ip_address, and device_name for registration auditing.
            db_refresh_token = RefreshToken(
                user_id=user.id,
                token_hash=hash_token(refresh_token),
                expires_at=expires_at,
            )
            self.db.add(db_refresh_token)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

        return {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    async def login(self, email: str, password: str) -> dict:
        """Verify credentials, issue JWT pair."""
        email = email.strip().lower()
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        # Reject inactive, soft-deleted, or incorrect password users
        if not user or user.is_deleted or not user.is_active or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        user.last_login_at = datetime.now(timezone.utc)

        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(subject=user.id)

        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        # TODO: Track user_agent, ip_address, and device_name for login auditing.
        db_refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh_token),
            expires_at=expires_at,
        )
        
        try:
            self.db.add(db_refresh_token)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    async def refresh_token(self, refresh_token: str) -> dict:
        """Rotate refresh token, issue new access token."""
        try:
            payload = decode_token(refresh_token)
            token_type = payload.get("type")
            if token_type != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type",
                )
            user_id = payload.get("sub")
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

        hashed = hash_token(refresh_token)
        result = await self.db.execute(select(RefreshToken).where(RefreshToken.token_hash == hashed))
        db_token = result.scalar_one_or_none()

        if not db_token or db_token.is_revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        expires_at = db_token.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        try:
            # Rotate token: revoke old one, create new one
            db_token.is_revoked = True
            db_token.revoked_at = datetime.now(timezone.utc)

            new_access_token = create_access_token(subject=user_id)
            new_refresh_token = create_refresh_token(subject=user_id)

            expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            # TODO: Track user_agent, ip_address, and device_name for refresh token rotation.
            db_new_token = RefreshToken(
                user_id=db_token.user_id,
                token_hash=hash_token(new_refresh_token),
                expires_at=expires_at,
            )
            self.db.add(db_new_token)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }

    async def logout(self, refresh_token: str) -> None:
        """Revoke refresh token."""
        hashed = hash_token(refresh_token)
        result = await self.db.execute(select(RefreshToken).where(RefreshToken.token_hash == hashed))
        db_token = result.scalar_one_or_none()
        if db_token:
            try:
                db_token.is_revoked = True
                db_token.revoked_at = datetime.now(timezone.utc)
                await self.db.commit()
            except Exception:
                await self.db.rollback()
                raise

    async def forgot_password(
        self, email: str, ip_address: str = "127.0.0.1", user_agent: str = "unknown"
    ) -> str | None:
        """Send password reset email."""
        email = email.strip().lower()
        result = await self.db.execute(
            select(User).where(
                User.email == email,
                User.is_deleted == False,
                User.is_active == True,
            )
        )
        user = result.scalar_one_or_none()
        if not user:
            # Silently return to prevent email enumeration
            return None

        # Rate limit password reset requests (max 3 per 10 minutes)
        ten_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=10)
        rate_result = await self.db.execute(
            select(func.count(PasswordResetToken.id)).where(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.created_at >= ten_minutes_ago,
            )
        )
        request_count = rate_result.scalar() or 0
        if request_count >= 3:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many password reset requests. Please try again later.",
            )

        # Generate a secure random token
        raw_token = secrets.token_urlsafe(32)
        hashed_token = hash_token(raw_token)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)

        db_token = PasswordResetToken(
            user_id=user.id,
            token_hash=hashed_token,
            expires_at=expires_at,
        )
        self.db.add(db_token)

        # Emit audit event
        audit_event = UserAuthAuditEvent(
            event_id=uuid.uuid4(),
            timestamp=datetime.now(timezone.utc),
            user_id=user.id,
            event_type="password_reset_request",
            action="forgot_password",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        logger.info(f"Audit Event: {audit_event}")

        try:
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

        return raw_token

    async def reset_password(
        self,
        token: str,
        new_password: str,
        ip_address: str = "127.0.0.1",
        user_agent: str = "unknown",
    ) -> None:
        """Reset password using token."""
        hashed_token = hash_token(token)
        result = await self.db.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.token_hash == hashed_token
            )
        )
        db_token = result.scalar_one_or_none()
        if not db_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )

        # Check expiration
        expires_at = db_token.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )

        # Check unused
        if db_token.used_at is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token has already been used",
            )

        # Lookup user
        user_result = await self.db.execute(
            select(User).where(User.id == db_token.user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user or user.is_deleted or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account is inactive or deleted",
            )

        # Hash new password and update user
        user.password_hash = hash_password(new_password)
        db_token.used_at = datetime.now(timezone.utc)

        # Revoke all refresh tokens for the user
        refresh_result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user.id,
                RefreshToken.is_revoked == False,
            )
        )
        refresh_tokens = refresh_result.scalars().all()
        for rt in refresh_tokens:
            rt.is_revoked = True
            rt.revoked_at = datetime.now(timezone.utc)

        # Emit audit event
        audit_event = UserAuthAuditEvent(
            event_id=uuid.uuid4(),
            timestamp=datetime.now(timezone.utc),
            user_id=user.id,
            event_type="password_reset_success",
            action="reset_password",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        logger.info(f"Audit Event: {audit_event}")

        try:
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

