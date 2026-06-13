"""Infrastructure module — models."""
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.base import BaseModel

class InfrastructureConfig(BaseModel):
    """External services and configurations mapping. Scaffolding only."""
    __tablename__ = "infrastructure_configs"
    service_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    config_key: Mapped[str] = mapped_column(String(100), nullable=False)
    config_value: Mapped[str] = mapped_column(Text, nullable=False)
