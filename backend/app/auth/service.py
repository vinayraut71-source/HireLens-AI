"""
Auth module — service layer.
PRD Section 10.1: bcrypt cost 12, JWT access 15m + refresh 7d.
"""
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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
from app.auth.models import RefreshToken


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

    async def forgot_password(self, email: str) -> None:
        """Send password reset email."""
        email = email.strip().lower()
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user or user.is_deleted or not user.is_active:
            # Silently return to prevent email enumeration
            return
        # TODO: Implement generation of password reset token and send reset email in a future sprint.

    async def reset_password(self, token: str, new_password: str) -> None:
        """Reset password using token."""
        # TODO: Implement validation of reset token and safe update of password in database, wrapped in a commit/rollback block in a future sprint.
        raise NotImplementedError("reset_password not active for core sprint 1 tasks")
