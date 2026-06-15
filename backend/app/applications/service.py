"""Applications module — service layer. Sprint 8 Application Tracking Engine."""
import logging
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from app.applications.models import Application, ApplicationPackage, OutcomeEvent, JobApplication, ApplicationTimelineEvent, OutcomeType
from app.jobs.models import Job
from app.resumes.models import ResumeVersion

logger = logging.getLogger(__name__)


# Legacy services kept for compatibility
class ApplicationService:
    def __init__(self, db: AsyncSession): self.db = db
    async def create(self, user_id, data) -> dict: raise NotImplementedError("Sprint 6")
    async def list_all(self, user_id, status=None) -> list: raise NotImplementedError("Sprint 6")
    async def get(self, user_id, app_id) -> dict: raise NotImplementedError("Sprint 6")
    async def update(self, user_id, app_id, data) -> dict: raise NotImplementedError("Sprint 6")
    async def delete(self, user_id, app_id) -> None: raise NotImplementedError("Sprint 6")
    async def get_stats(self, user_id) -> dict: raise NotImplementedError("Sprint 6")
    async def record_outcome(self, user_id, app_id, event_type, metadata=None) -> dict: raise NotImplementedError("Sprint 6")
    async def list_outcomes(self, user_id, app_id) -> list: raise NotImplementedError("Sprint 6")

class PackageService:
    def __init__(self, db: AsyncSession): self.db = db
    async def create_package(self, user_id, job_id) -> dict: raise NotImplementedError("Phase 2")
    async def list_packages(self, user_id) -> list: raise NotImplementedError("Phase 2")
    async def get_package(self, user_id, pkg_id) -> dict: raise NotImplementedError("Phase 2")
    async def approve(self, user_id, pkg_id) -> dict: raise NotImplementedError("Phase 2")
    async def reject(self, user_id, pkg_id) -> dict: raise NotImplementedError("Phase 2")
    async def submit(self, user_id, pkg_id) -> dict: raise NotImplementedError("Phase 2")


class ApplicationTrackingService:
    """
    Sprint 8: Application Tracking Engine Service.
    Enforces ownership validation, transaction safety, soft-delete protection, and idempotent status updates.
    """

    ALLOWED_STATUSES = {
        "draft", "saved", "applied", "in_review", "assessment", "interview", "offer", "rejected", "withdrawn"
    }

    VALID_TRANSITIONS = {
        "draft": {"saved", "withdrawn"},
        "saved": {"applied", "withdrawn"},
        "applied": {"in_review", "rejected", "withdrawn"},
        "in_review": {"assessment", "rejected", "withdrawn"},
        "assessment": {"interview", "rejected", "withdrawn"},
        "interview": {"offer", "rejected", "withdrawn"},
        "offer": {"withdrawn"},
        "rejected": {"withdrawn"},
        "withdrawn": set()  # Terminal state
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_application(self, user_id: uuid.UUID, data: dict) -> JobApplication:
        """
        Track a new application.
        Validates that the associated Job and ResumeVersion exist, belong to the user, and are not soft-deleted.
        """
        job_id = data["job_id"]
        resume_version_id = data["resume_version_id"]
        status = data.get("status", "draft")

        if status not in self.ALLOWED_STATUSES:
            raise HTTPException(status_code=400, detail=f"Invalid initial status: {status}")

        # 1. Validate Job
        stmt_job = select(Job).where(Job.id == job_id, Job.user_id == user_id, Job.is_deleted == False)
        res_job = await self.db.execute(stmt_job)
        job = res_job.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Associated Job not found or is soft-deleted")

        # 2. Validate ResumeVersion
        stmt_resume = select(ResumeVersion).where(ResumeVersion.id == resume_version_id, ResumeVersion.user_id == user_id, ResumeVersion.is_deleted == False)
        res_resume = await self.db.execute(stmt_resume)
        if not res_resume.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Associated ResumeVersion not found or is soft-deleted")

        # Format salary string for snapshot
        salary_str = None
        if job.salary_min is not None and job.salary_max is not None:
            salary_str = f"{job.salary_min} - {job.salary_max}"
        elif job.salary_min is not None:
            salary_str = f"{job.salary_min}+"
        elif job.salary_max is not None:
            salary_str = f"Up to {job.salary_max}"

        job_snapshot = {
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "salary": salary_str,
            "url": job.source_url
        }

        # Determine outcome type from status
        status_to_outcome = {
            "draft": OutcomeType.unknown,
            "saved": OutcomeType.unknown,
            "applied": OutcomeType.no_response,
            "in_review": OutcomeType.no_response,
            "assessment": OutcomeType.no_response,
            "interview": OutcomeType.interviewed,
            "offer": OutcomeType.offered,
            "rejected": OutcomeType.rejected,
            "withdrawn": OutcomeType.unknown,
        }
        initial_outcome = status_to_outcome.get(status, OutcomeType.unknown)

        now = datetime.now(tz=timezone.utc)
        applied_at = now if status == "applied" else None
        interview_at = now if status == "interview" else None
        offer_at = now if status == "offer" else None
        rejection_at = now if status == "rejected" else None
        first_response_at = None
        if status in {"in_review", "assessment", "interview", "offer", "rejected"}:
            first_response_at = now

        application = JobApplication(
            user_id=user_id,
            job_id=job_id,
            resume_version_id=resume_version_id,
            status=status,
            outcome_type=initial_outcome,
            job_snapshot=job_snapshot,
            source=data.get("source"),
            notes=data.get("notes"),
            applied_at=applied_at,
            first_response_at=first_response_at,
            interview_at=interview_at,
            offer_at=offer_at,
            rejection_at=rejection_at
        )

        timeline_event = ApplicationTimelineEvent(
            event_type="created",
            previous_status=None,
            new_status=status,
            notes="Application tracked"
        )
        application.timeline_events.append(timeline_event)

        try:
            self.db.add(application)
            await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to create application: {str(e)}", exc_info=True)
            await self.db.rollback()
            raise HTTPException(status_code=500, detail="Failed to save application tracking record.")

        # Re-fetch with eager loading to avoid MissingGreenlet on timeline_events
        stmt_reload = (
            select(JobApplication)
            .options(selectinload(JobApplication.timeline_events))
            .where(JobApplication.id == application.id)
        )
        res_reload = await self.db.execute(stmt_reload)
        return res_reload.scalar_one()

    async def update_status(
        self, user_id: uuid.UUID, application_id: uuid.UUID, new_status: str, notes: str | None = None, outcome_type: str | None = None
    ) -> JobApplication:
        """
        Updates an application's status.
        Enforces transition validity, ownership check, idempotency, and transaction safety.
        """
        new_status = new_status.lower().strip()
        if new_status not in self.ALLOWED_STATUSES:
            raise HTTPException(status_code=400, detail=f"Invalid status: {new_status}")

        # Fetch application and check ownership/soft-delete
        application = await self.get_application(user_id, application_id)

        # Determine new outcome type
        if outcome_type is not None:
            outcome_type = outcome_type.lower().strip()
            if outcome_type not in {o.value for o in OutcomeType}:
                raise HTTPException(status_code=400, detail=f"Invalid outcome type: {outcome_type}")
            new_outcome = OutcomeType(outcome_type)
        else:
            status_to_outcome = {
                "draft": OutcomeType.unknown,
                "saved": OutcomeType.unknown,
                "applied": OutcomeType.no_response,
                "in_review": OutcomeType.no_response,
                "assessment": OutcomeType.no_response,
                "interview": OutcomeType.interviewed,
                "offer": OutcomeType.offered,
                "rejected": OutcomeType.rejected,
                "withdrawn": OutcomeType.unknown,
            }
            new_outcome = status_to_outcome.get(new_status, application.outcome_type)

        # Idempotent status check
        if application.status == new_status and application.outcome_type == new_outcome:
            return application

        # Validate transition flow if status is actually changing
        old_status = application.status
        if old_status != new_status:
            valid_destinations = self.VALID_TRANSITIONS.get(old_status, set())
            if new_status not in valid_destinations:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status transition from '{old_status}' to '{new_status}'."
                )

        # Update status, outcome_type and timeline
        application.status = new_status
        application.outcome_type = new_outcome
        now = datetime.now(tz=timezone.utc)

        # Analytics timestamps updates (only if status is actually changing)
        if old_status != new_status:
            if new_status == "applied":
                application.applied_at = now
            elif new_status == "interview":
                application.interview_at = now
            elif new_status == "offer":
                application.offer_at = now
            elif new_status == "rejected":
                application.rejection_at = now

            # Update first_response_at on first response state
            if new_status in {"in_review", "assessment", "interview", "offer", "rejected"}:
                if application.applied_at is not None and application.first_response_at is None:
                    application.first_response_at = now

        timeline_event = None
        if old_status != new_status:
            timeline_event = ApplicationTimelineEvent(
                application_id=application_id,
                event_type="status_change",
                previous_status=old_status,
                new_status=new_status,
                notes=notes
            )

        try:
            if timeline_event:
                self.db.add(timeline_event)
            await self.db.commit()
            await self.db.refresh(application)
        except Exception as e:
            logger.error(f"Failed to update application status: {str(e)}", exc_info=True)
            await self.db.rollback()
            raise HTTPException(status_code=500, detail="Failed to update application status.")

        return application

    async def get_application(self, user_id: uuid.UUID, application_id: uuid.UUID) -> JobApplication:
        """Fetch application with ownership and soft-delete checks."""
        stmt = (
            select(JobApplication)
            .options(selectinload(JobApplication.timeline_events))
            .join(Job, JobApplication.job_id == Job.id)
            .join(ResumeVersion, JobApplication.resume_version_id == ResumeVersion.id)
            .where(
                JobApplication.id == application_id,
                JobApplication.user_id == user_id,
                Job.is_deleted == False,
                ResumeVersion.is_deleted == False
            )
        )
        result = await self.db.execute(stmt)
        application = result.scalar_one_or_none()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found or associated resources deleted")
        return application

    async def list_applications(self, user_id: uuid.UUID) -> list[JobApplication]:
        """List user applications. Excludes those with soft-deleted jobs/resumes."""
        stmt = (
            select(JobApplication)
            .options(selectinload(JobApplication.timeline_events))
            .join(Job, JobApplication.job_id == Job.id)
            .join(ResumeVersion, JobApplication.resume_version_id == ResumeVersion.id)
            .where(
                JobApplication.user_id == user_id,
                Job.is_deleted == False,
                ResumeVersion.is_deleted == False
            )
            .order_by(JobApplication.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_timeline(self, user_id: uuid.UUID, application_id: uuid.UUID) -> list[ApplicationTimelineEvent]:
        """Fetch timeline events for an application. Enforces ownership and soft-delete."""
        # Enforce validation
        await self.get_application(user_id, application_id)

        stmt = (
            select(ApplicationTimelineEvent)
            .where(ApplicationTimelineEvent.application_id == application_id)
            .order_by(ApplicationTimelineEvent.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
