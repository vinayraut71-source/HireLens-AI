"""
Central import file for SQLAlchemy models to register them on Base.metadata.
Used by Alembic.
"""
from app.shared.base import Base

# Import all domain models
from app.auth.models import RefreshToken, PasswordResetToken
from app.users.models import User, UserPreference
from app.resumes.models import (
    ResumeProfile,
    ResumeVersion,
    ResumeVersionEmbedding,
    AtsScoreHistory,
    MatchScoreHistory,
    ATSAnalysis,
)
from app.jobs.models import Job, JobEmbedding, MatchResult, SkillGap, JobMatch, SkillGapAnalysis
from app.applications.models import Application, ApplicationPackage, OutcomeEvent, JobApplication, ApplicationTimelineEvent
from app.analytics.models import UserAnalyticsSnapshot, AnalyticsSnapshot, AnalyticsInsight
from app.audit.models import AgentAuditLog
from app.roadmap.models import LearningRoadmap, RoadmapModule, CareerRoadmap, RoadmapMilestone
from app.recommendations.models import RecommendationSignal
from app.ai.models import AgentRun
from app.infrastructure.models import InfrastructureConfig

# B2B Models
from app.models.b2b import Company, Recruiter, CompanyUser, JobPosting, CandidateMatch
