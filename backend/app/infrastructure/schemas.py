"""Infrastructure module — Pydantic schemas."""
from uuid import UUID
from pydantic import BaseModel

class HealthCheckResponse(BaseModel):
    status: str
    postgres: str
    redis: str
    minio: str

class ConfigResponse(BaseModel):
    id: UUID
    service_name: str
    config_key: str
    config_value: str
    class Config: from_attributes = True
