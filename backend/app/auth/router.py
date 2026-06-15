"""
Auth module — API router.
PRD Section 8.2: Authentication Endpoints.
"""
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from typing import Annotated
from fastapi import APIRouter, Depends, status, Request, HTTPException

from app.auth.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    TokenResponse,
)
from app.core.dependencies import DBSession, get_current_active_user
from app.auth.service import AuthService
from app.users.models import User
from app.users.schemas import UserResponse

# Simple in-memory rate limiter for forgot-password IP requests: max 10 requests per minute per IP.
ip_forgot_password_history = defaultdict(list)


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user account",
    description="Register with email/password. Returns JWT tokens.",
)
async def register(body: RegisterRequest, db: DBSession):
    """US-001: Sign up with email/password."""
    # TODO: Implement rate limiting for user registration to prevent abuse/spam.
    auth_service = AuthService(db)
    return await auth_service.register(
        email=body.email, password=body.password, full_name=body.full_name
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive tokens",
    description="Authenticate and receive access + refresh JWT tokens.",
)
async def login(body: LoginRequest, db: DBSession):
    # TODO: Implement rate limiting for login attempts to mitigate brute-force attacks.
    auth_service = AuthService(db)
    return await auth_service.login(email=body.email, password=body.password)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Exchange a refresh token for a new access token.",
)
async def refresh(body: RefreshRequest, db: DBSession):
    auth_service = AuthService(db)
    return await auth_service.refresh_token(refresh_token=body.refresh_token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Invalidate refresh token",
    description="Invalidate and revoke the provided refresh token to securely log out the user.",
)
async def logout(body: RefreshRequest, db: DBSession):
    auth_service = AuthService(db)
    await auth_service.logout(refresh_token=body.refresh_token)


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Send password reset email",
    description="Generate and send a password reset link to the user's email address if it exists.",
)
async def forgot_password(request: Request, body: ForgotPasswordRequest, db: DBSession):
    ip_address = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent", "unknown")

    # Rate-limit IP addresses to prevent abuse (max 10 requests per minute per IP)
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=1)
    ip_forgot_password_history[ip_address] = [
        ts for ts in ip_forgot_password_history[ip_address] if ts > cutoff
    ]
    if len(ip_forgot_password_history[ip_address]) >= 10:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many password reset requests from this IP. Please try again later.",
        )
    ip_forgot_password_history[ip_address].append(now)

    auth_service = AuthService(db)
    await auth_service.forgot_password(
        email=body.email, ip_address=ip_address, user_agent=user_agent
    )
    return {"detail": "Password reset link sent if email exists"}


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset password with token",
    description="Reset the user's password using a valid reset token.",
)
async def reset_password(request: Request, body: ResetPasswordRequest, db: DBSession):
    ip_address = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent", "unknown")

    auth_service = AuthService(db)
    await auth_service.reset_password(
        token=body.token,
        new_password=body.new_password,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return {"detail": "Password reset successful"}


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Returns the authenticated user's profile.",
)
async def get_me(current_user: Annotated[User, Depends(get_current_active_user)]):
    return current_user
