"""
Recommendation Event Contracts.
Contracts capturing user preferences and feedback signals for vector indexing.
"""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

@dataclass(frozen=True)
class RecommendationFeedbackEvent:
    event_id: UUID
    timestamp: datetime
    user_id: UUID
    signal_type: str  # job, skill, resume_suggestion
    signal_key: str
    interaction_weight: float  # click=1.0, save=3.0, dismiss=-2.0
