"""AI Layer — models. PRD Section 7.2 + 9.0."""
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.base import BaseModel

class AgentRun(BaseModel):
    """Model tracking individual AI agent execution sessions."""
    __tablename__ = "agent_runs"
    agent_name: Mapped[str] = mapped_column(String(50), nullable=False)
    input_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", server_default="pending")
