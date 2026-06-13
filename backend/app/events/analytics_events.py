"""
Analytics Event Contracts.
Contracts for tracking system usage, funnel metrics, and user interactions.
"""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

@dataclass(frozen=True)
class AnalyticsEvent:
    event_id: UUID
    timestamp: datetime
    user_id: UUID

@dataclass(frozen=True)
class ApplicationFunnelEvent(AnalyticsEvent):
    application_id: UUID
    previous_status: str
    new_status: str

@dataclass(frozen=True)
class FeatureUsageEvent(AnalyticsEvent):
    feature_name: str
    interaction_details: dict
