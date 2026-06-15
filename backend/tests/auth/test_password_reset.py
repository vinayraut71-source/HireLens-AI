import pytest
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.auth.models import PasswordResetToken, RefreshToken
from app.users.models import User
from app.auth.service import AuthService

pytestmark = pytest.mark.asyncio


async def test_valid_password_reset_flow(client: AsyncClient, db_session: AsyncSession):
    # 1. Register a user
    register_payload = {
        "email": "reset_user@example.com",
        "password": "old_password_123",
        "full_name": "Reset User",
    }
    register_resp = await client.post("/api/v1/auth/register", json=register_payload)
    assert register_resp.status_code == 201
    user_id = register_resp.json()["id"]

    # 2. Request forgot-password using the API
    forgot_resp = await client.post(
        "/api/v1/auth/forgot-password", json={"email": "reset_user@example.com"}
    )
    assert forgot_resp.status_code == 202
    assert forgot_resp.json()["detail"] == "Password reset link sent if email exists"

    # 3. Call the service layer forgot_password directly to get the raw token (since it is not returned in API response)
    auth_service = AuthService(db_session)
    raw_token = await auth_service.forgot_password(email="reset_user@example.com")
    assert raw_token is not None

    # 4. Use the raw token to reset password via the API
    reset_resp = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "new_password_456"},
    )
    assert reset_resp.status_code == 200
    assert reset_resp.json()["detail"] == "Password reset successful"

    # 5. Verify old password no longer works for login
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "reset_user@example.com", "password": "old_password_123"},
    )
    assert login_resp.status_code == 401

    # 6. Verify new password works for login
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "reset_user@example.com", "password": "new_password_456"},
    )
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()


async def test_expired_token(client: AsyncClient, db_session: AsyncSession):
    # Register user
    register_payload = {
        "email": "expired_user@example.com",
        "password": "password123",
        "full_name": "Expired User",
    }
    await client.post("/api/v1/auth/register", json=register_payload)

    # Generate token
    auth_service = AuthService(db_session)
    raw_token = await auth_service.forgot_password(email="expired_user@example.com")
    assert raw_token is not None

    # Retrieve and manually expire the token in database
    from app.core.security import hash_token
    hashed_token = hash_token(raw_token)
    stmt = select(PasswordResetToken).where(PasswordResetToken.token_hash == hashed_token)
    result = await db_session.execute(stmt)
    db_token = result.scalar_one()
    db_token.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    await db_session.commit()

    # Attempt to reset password
    reset_resp = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "new_password_456"},
    )
    assert reset_resp.status_code == 400
    assert reset_resp.json()["detail"] == "Invalid or expired reset token"


async def test_reused_token(client: AsyncClient, db_session: AsyncSession):
    # Register user
    register_payload = {
        "email": "reused_user@example.com",
        "password": "password123",
        "full_name": "Reused User",
    }
    await client.post("/api/v1/auth/register", json=register_payload)

    # Generate token
    auth_service = AuthService(db_session)
    raw_token = await auth_service.forgot_password(email="reused_user@example.com")
    assert raw_token is not None

    # Reset password first time
    reset_resp = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "new_password_456"},
    )
    assert reset_resp.status_code == 200

    # Reset password second time with same token
    reset_resp = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "new_password_789"},
    )
    assert reset_resp.status_code == 400
    assert reset_resp.json()["detail"] == "Reset token has already been used"


async def test_invalid_token(client: AsyncClient):
    reset_resp = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": "some_fake_nonexistent_token", "new_password": "new_password_123"},
    )
    assert reset_resp.status_code == 400
    assert reset_resp.json()["detail"] == "Invalid or expired reset token"


async def test_refresh_token_revocation(client: AsyncClient, db_session: AsyncSession):
    # 1. Register a user and log in to get access/refresh tokens
    register_payload = {
        "email": "revoke_user@example.com",
        "password": "password123",
        "full_name": "Revocation User",
    }
    await client.post("/api/v1/auth/register", json=register_payload)

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "revoke_user@example.com", "password": "password123"},
    )
    assert login_resp.status_code == 200
    refresh_token = login_resp.json()["refresh_token"]

    # Verify refresh token works initially
    refresh_resp = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert refresh_resp.status_code == 200
    new_refresh_token = refresh_resp.json()["refresh_token"]

    # 2. Reset password
    auth_service = AuthService(db_session)
    raw_token = await auth_service.forgot_password(email="revoke_user@example.com")
    
    reset_resp = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "new_password_123"},
    )
    assert reset_resp.status_code == 200

    # 3. Attempt to use active refresh token
    refresh_resp = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": new_refresh_token}
    )
    assert refresh_resp.status_code == 401
    assert refresh_resp.json()["detail"] == "Invalid or expired refresh token"


async def test_email_enumeration_protection(client: AsyncClient, db_session: AsyncSession):
    # Request forgot password for an email that does not exist
    forgot_resp = await client.post(
        "/api/v1/auth/forgot-password", json={"email": "nonexistent@example.com"}
    )
    # Must return 202 Accepted and the generic message
    assert forgot_resp.status_code == 202
    assert forgot_resp.json()["detail"] == "Password reset link sent if email exists"

    # Verify that no token was generated in the database
    stmt = select(PasswordResetToken)
    result = await db_session.execute(stmt)
    tokens = result.scalars().all()
    # Check that none of the tokens belong to a nonexistent user/email
    # (Actually, there shouldn't be any tokens unless created by other test threads,
    # but we can filter by matching emails or join)
    for token in tokens:
        # Resolve user email
        user_stmt = select(User).where(User.id == token.user_id)
        user_result = await db_session.execute(user_stmt)
        user = user_result.scalar_one()
        assert user.email != "nonexistent@example.com"


async def test_transaction_rollback(client: AsyncClient, db_session: AsyncSession, monkeypatch):
    # 1. Register a user
    register_payload = {
        "email": "rollback_user@example.com",
        "password": "password123",
        "full_name": "Rollback User",
    }
    await client.post("/api/v1/auth/register", json=register_payload)

    # 2. Generate token and refresh token
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "rollback_user@example.com", "password": "password123"},
    )
    assert login_resp.status_code == 200
    refresh_token = login_resp.json()["refresh_token"]

    auth_service = AuthService(db_session)
    raw_token = await auth_service.forgot_password(email="rollback_user@example.com")
    assert raw_token is not None

    # Get hashed token to check status later
    from app.core.security import hash_token
    hashed_token = hash_token(raw_token)

    # 3. Mock hash_password to raise a ValueError during reset execution
    def mock_hash_password(password: str) -> str:
        raise ValueError("Simulated hashing failure")

    monkeypatch.setattr("app.auth.service.hash_password", mock_hash_password)

    # 4. Attempt to reset password - should fail due to the mock
    with pytest.raises(ValueError, match="Simulated hashing failure"):
        await auth_service.reset_password(token=raw_token, new_password="new_password_123")

    # 5. Clear dependency override and check database state. Since the service method raised
    # an exception before commit (or inside the try-except where it rolled back),
    # the password_reset_token's used_at must still be None, and the refresh token must NOT be revoked.
    
    # We retrieve the token and refresh token directly using the session
    # (Wait, if the session rolled back, the changes shouldn't be flushed/persisted).
    # Refresh session state
    db_session.expire_all()
    
    token_stmt = select(PasswordResetToken).where(PasswordResetToken.token_hash == hashed_token)
    token_res = await db_session.execute(token_stmt)
    db_token = token_res.scalar_one()
    assert db_token.used_at is None

    # Check refresh tokens for the user
    user_stmt = select(User).where(User.email == "rollback_user@example.com")
    user_res = await db_session.execute(user_stmt)
    user = user_res.scalar_one()

    rt_stmt = select(RefreshToken).where(RefreshToken.user_id == user.id)
    rt_res = await db_session.execute(rt_stmt)
    db_rt = rt_res.scalars().all()
    # At least one active refresh token should exist and not be revoked
    active_rts = [rt for rt in db_rt if not rt.is_revoked]
    assert len(active_rts) > 0
