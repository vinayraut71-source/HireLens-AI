"""
Shared type aliases and generic response models.
"""
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


# --- Generic API response wrappers ---

class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated list response per PRD Section 8.1."""

    data: list[T]
    total: int
    page: int
    limit: int

    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    """Standard error response per PRD Section 8.1."""

    detail: str
    code: str


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    app_name: str
    environment: str


# --- Shared schema base ---

class BaseSchema(BaseModel):
    """Base schema with ORM mode enabled."""

    model_config = ConfigDict(from_attributes=True)


class TimestampSchema(BaseSchema):
    """Schema with timestamp fields."""

    created_at: Any = None
    updated_at: Any = None


class IDSchema(BaseSchema):
    """Schema with UUID id field."""

    id: UUID
