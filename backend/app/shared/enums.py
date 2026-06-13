"""
Shared enumerations used across all domain modules.
Derived from PRD Section 7 and Section 8 specifications.
"""
from enum import Enum


# --- User & Plan ---

class PlanTier(str, Enum):
    FREE = "free"
    PRO = "pro"
    PREMIUM = "premium"


# --- Resume ---

class ResumeVersionSource(str, Enum):
    UPLOAD = "upload"
    EDIT = "edit"
    AI_TAILOR = "ai_tailor"
    DUPLICATE = "duplicate"


class ResumeVersionStatus(str, Enum):
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


# --- Application ---

class ApplicationStatus(str, Enum):
    SAVED = "saved"
    APPLIED = "applied"
    VIEWED = "viewed"
    REJECTED = "rejected"
    PHONE_SCREEN = "phone_screen"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEW_PASSED = "interview_passed"
    OFFER_RECEIVED = "offer_received"
    OFFER_ACCEPTED = "offer_accepted"
    WITHDRAWN = "withdrawn"


# --- Application Package (Human-in-the-Loop) ---

class ApprovalStatus(str, Enum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUBMITTED = "submitted"
    EXPIRED = "expired"


# --- Outcome Events ---

class OutcomeEventType(str, Enum):
    APPLIED = "applied"
    VIEWED = "viewed"
    REJECTED = "rejected"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEW_PASSED = "interview_passed"
    OFFER_RECEIVED = "offer_received"
    OFFER_ACCEPTED = "offer_accepted"


# --- Skill Gap ---

class SkillGapPriority(str, Enum):
    CRITICAL = "critical"
    IMPORTANT = "important"
    NICE_TO_HAVE = "nice_to_have"


class SkillGapStatus(str, Enum):
    IDENTIFIED = "identified"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class SkillGapCategory(str, Enum):
    TECHNICAL = "technical"
    SOFT = "soft"
    DOMAIN = "domain"


# --- Roadmap ---

class RoadmapStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ModuleStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


# --- Remote Preference ---

class RemotePreference(str, Enum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"
    ANY = "any"


# --- Agent Audit ---

class AgentName(str, Enum):
    RESUME_AGENT = "resume_agent"
    MATCHING_AGENT = "matching_agent"
    COACHING_AGENT = "coaching_agent"
    DISCOVERY_AGENT = "discovery_agent"
    FEEDBACK_AGENT = "feedback_agent"


class AgentActionType(str, Enum):
    RESUME_ANALYZED = "resume_analyzed"
    ATS_SCORE_GENERATED = "ats_score_generated"
    JOB_MATCHED = "job_matched"
    ROADMAP_GENERATED = "roadmap_generated"
    RESUME_TAILORED = "resume_tailored"
    COVER_LETTER_GENERATED = "cover_letter_generated"
    JOB_DISCOVERED = "job_discovered"
    APPLICATION_SUGGESTED = "application_suggested"
    USER_APPROVED = "user_approved"
    USER_REJECTED = "user_rejected"
    APPLICATION_SUBMITTED = "application_submitted"


class AgentApprovalStatus(str, Enum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


# --- ATS Score ---

class AtsScoredBy(str, Enum):
    SYSTEM = "system"
    USER_REQUEST = "user_request"
    AUTO_ON_EDIT = "auto_on_edit"


# --- Recommendation Signals ---

class SignalType(str, Enum):
    JOB = "job"
    SKILL = "skill"
    RESUME_SUGGESTION = "resume_suggestion"


# --- B2B ---

class RecruiterRole(str, Enum):
    ADMIN = "admin"
    RECRUITER = "recruiter"
    VIEWER = "viewer"


class CompanySize(str, Enum):
    STARTUP = "startup"
    SMB = "smb"
    ENTERPRISE = "enterprise"


class CandidateVisibility(str, Enum):
    PRIVATE = "private"
    ANONYMIZED = "anonymized"
    FULL = "full"


class JobPostingStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"


class RecruiterCandidateStatus(str, Enum):
    NEW = "new"
    SHORTLISTED = "shortlisted"
    REJECTED = "rejected"
    CONTACTED = "contacted"
