"""Roadmap module — service layer. Sprint 7 Career Roadmap Generator."""
import logging
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from app.roadmap.models import CareerRoadmap, RoadmapMilestone
from app.jobs.models import Job, JobMatch, SkillGapAnalysis
from app.resumes.models import ResumeVersion

logger = logging.getLogger(__name__)


class RoadmapService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_roadmap(self, user_id: uuid.UUID, match_id: uuid.UUID) -> CareerRoadmap:
        """
        Generate a deterministic learning roadmap for a job match.

        1. Validate job match ownership and verify associated job/resume are not soft-deleted.
        2. Check for cached roadmap to ensure idempotency.
        3. Fetch skill gaps, sorted by roadmap_priority_score descending.
        4. Create milestones based on priority:
           - critical: 4 weeks
           - high: 3 weeks
           - medium: 2 weeks
           - low: 1 week
        5. Persist and return.
        """
        # --- 1. Validate JobMatch and check soft-delete protection ---
        stmt = (
            select(JobMatch)
            .join(Job, JobMatch.job_id == Job.id)
            .join(ResumeVersion, JobMatch.resume_version_id == ResumeVersion.id)
            .where(
                JobMatch.id == match_id,
                JobMatch.user_id == user_id,
                Job.is_deleted == False,
                ResumeVersion.is_deleted == False,
            )
        )
        result = await self.db.execute(stmt)
        job_match = result.scalar_one_or_none()
        if not job_match:
            raise HTTPException(status_code=404, detail="Job match not found or associated resources deleted")

        # --- 2. Check Cache (Idempotency) ---
        cached = await self._get_cached_roadmap(match_id)
        if cached:
            return cached

        # --- 3. Fetch Skill Gaps ordered by roadmap_priority_score desc ---
        stmt_gaps = (
            select(SkillGapAnalysis)
            .where(SkillGapAnalysis.job_match_id == match_id)
            .order_by(SkillGapAnalysis.roadmap_priority_score.desc())
        )
        gaps_result = await self.db.execute(stmt_gaps)
        gaps = list(gaps_result.scalars().all())

        # --- 4. Generate Milestones and Weeks ---
        milestones = []
        total_weeks = 0

        # Mapping priority to weeks
        weeks_map = {
            "critical": 4,
            "high": 3,
            "medium": 2,
            "low": 1
        }

        for index, gap in enumerate(gaps):
            weeks = weeks_map.get(gap.learning_priority.lower(), 2)
            milestone = RoadmapMilestone(
                skill_gap_id=gap.id,
                milestone_order=index + 1,
                milestone_title=f"Learn {gap.missing_skill}",
                estimated_weeks=weeks,
                priority_score=gap.roadmap_priority_score,
                completion_status="pending"
            )
            milestones.append(milestone)
            total_weeks += weeks

        roadmap = CareerRoadmap(
            user_id=user_id,
            resume_version_id=job_match.resume_version_id,
            job_match_id=match_id,
            generated_at=datetime.now(tz=timezone.utc),
            total_estimated_weeks=total_weeks,
            roadmap_status="active",
            milestones=milestones
        )

        try:
            self.db.add(roadmap)
            await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to generate roadmap for match {match_id}: {str(e)}", exc_info=True)
            await self.db.rollback()
            raise HTTPException(status_code=500, detail="Failed to create roadmap.")

        return await self._get_cached_roadmap(match_id)

    async def get_roadmap(self, user_id: uuid.UUID, match_id: uuid.UUID) -> CareerRoadmap:
        """Fetch cached roadmap for a job match with ownership and soft-delete protection."""
        # Check match first to verify ownership and soft-deletes
        stmt_match = (
            select(JobMatch)
            .join(Job, JobMatch.job_id == Job.id)
            .join(ResumeVersion, JobMatch.resume_version_id == ResumeVersion.id)
            .where(
                JobMatch.id == match_id,
                JobMatch.user_id == user_id,
                Job.is_deleted == False,
                ResumeVersion.is_deleted == False,
            )
        )
        match_res = await self.db.execute(stmt_match)
        if not match_res.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Job match not found or associated resources deleted")

        roadmap = await self._get_cached_roadmap(match_id)
        if not roadmap:
            raise HTTPException(status_code=404, detail="Roadmap not generated yet for this job match")

        return roadmap

    async def patch_milestone(
        self, user_id: uuid.UUID, roadmap_id: uuid.UUID, milestone_id: uuid.UUID, status: str
    ) -> RoadmapMilestone:
        """Update a milestone's completion status. Enforces roadmap ownership."""
        # Verify roadmap ownership
        stmt_roadmap = select(CareerRoadmap).where(
            CareerRoadmap.id == roadmap_id,
            CareerRoadmap.user_id == user_id
        )
        roadmap_res = await self.db.execute(stmt_roadmap)
        roadmap = roadmap_res.scalar_one_or_none()
        if not roadmap:
            raise HTTPException(status_code=404, detail="Roadmap not found")

        # Verify milestone belongs to the roadmap
        stmt_milestone = select(RoadmapMilestone).where(
            RoadmapMilestone.id == milestone_id,
            RoadmapMilestone.roadmap_id == roadmap_id
        )
        milestone_res = await self.db.execute(stmt_milestone)
        milestone = milestone_res.scalar_one_or_none()
        if not milestone:
            raise HTTPException(status_code=404, detail="Milestone not found")

        # Update status
        milestone.completion_status = status

        try:
            await self.db.commit()
            await self.db.refresh(milestone)
        except Exception as e:
            logger.error(f"Failed to update milestone {milestone_id}: {str(e)}", exc_info=True)
            await self.db.rollback()
            raise HTTPException(status_code=500, detail="Failed to update milestone.")

        return milestone

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    async def _get_cached_roadmap(self, match_id: uuid.UUID) -> CareerRoadmap | None:
        """Fetch cached roadmap by job_match_id with milestones eager loaded."""
        stmt = (
            select(CareerRoadmap)
            .options(selectinload(CareerRoadmap.milestones))
            .where(CareerRoadmap.job_match_id == match_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
