"""Jobs module — service layer. Sprint 5: Job CRUD + Intelligent Job Matching."""
import re
import hashlib
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.jobs.models import Job, JobMatch
from app.resumes.models import ResumeProfile, ResumeVersion, ATSAnalysis
from app.resumes.service import (
    JobDescriptionAnalyzer,
    ATSScoringService,
    ResumeVersionService,
)

logger = logging.getLogger(__name__)


class JobService:
    """Handles database transactions for Job CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_job(self, user_id: uuid.UUID, data: dict) -> Job:
        """Create a new saved job."""
        job = Job(
            user_id=user_id,
            title=data["title"],
            company=data.get("company"),
            description=data["description"],
            source_url=data.get("source_url"),
            location=data.get("location"),
            remote_type=data.get("remote_type"),
            salary_min=data.get("salary_min"),
            salary_max=data.get("salary_max"),
            is_saved=True,
        )
        try:
            self.db.add(job)
            await self.db.commit()
            await self.db.refresh(job)
        except Exception as e:
            logger.error(f"Failed to create job for user {user_id}: {str(e)}", exc_info=True)
            await self.db.rollback()
            raise HTTPException(status_code=500, detail="Failed to save job.")
        return job

    async def list_jobs(self, user_id: uuid.UUID) -> list[Job]:
        """List all non-deleted jobs belonging to the user."""
        stmt = select(Job).where(
            Job.user_id == user_id,
            Job.is_deleted == False,
        ).order_by(Job.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_job(self, user_id: uuid.UUID, job_id: uuid.UUID) -> Job:
        """Get a single job by ID, enforcing ownership."""
        stmt = select(Job).where(
            Job.id == job_id,
            Job.user_id == user_id,
            Job.is_deleted == False,
        )
        result = await self.db.execute(stmt)
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job

    async def update_job(self, user_id: uuid.UUID, job_id: uuid.UUID, data: dict) -> Job:
        """Update job fields. Ownership enforced."""
        job = await self.get_job(user_id, job_id)
        for field in ("title", "company", "description", "is_saved"):
            if field in data and data[field] is not None:
                setattr(job, field, data[field])
        try:
            await self.db.commit()
            await self.db.refresh(job)
        except Exception as e:
            logger.error(f"Failed to update job {job_id}: {str(e)}", exc_info=True)
            await self.db.rollback()
            raise HTTPException(status_code=500, detail="Failed to update job.")
        return job

    async def delete_job(self, user_id: uuid.UUID, job_id: uuid.UUID) -> None:
        """Soft-delete a job. Ownership enforced."""
        job = await self.get_job(user_id, job_id)
        try:
            job.is_deleted = True
            job.deleted_at = datetime.now(tz=timezone.utc)
            await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to delete job {job_id}: {str(e)}", exc_info=True)
            await self.db.rollback()
            raise HTTPException(status_code=500, detail="Failed to delete job.")


class JobMatchingService:
    """
    Sprint 5: Deterministic Job Matching Service.

    Computes an overall match score (0-100) from:
      - Skills overlap (30%)
      - Experience alignment (25%)
      - Education alignment (20%)
      - Keyword overlap (15%)
      - ATS score contribution (10%)

    All scoring is deterministic. No Gemini / LLM calls.
    Identical inputs produce identical outputs.
    """

    # Weights for overall match score
    WEIGHT_SKILLS = 0.30
    WEIGHT_EXPERIENCE = 0.25
    WEIGHT_EDUCATION = 0.20
    WEIGHT_KEYWORDS = 0.15
    WEIGHT_ATS = 0.10

    EDU_LEVELS = {"none": 0, "bachelor's": 1, "master's": 2, "phd": 3}

    def __init__(self, db: AsyncSession):
        self.db = db

    async def match(
        self,
        user_id: uuid.UUID,
        job_id: uuid.UUID,
        resume_version_id: uuid.UUID,
    ) -> JobMatch:
        """
        Compute a deterministic match between a resume version and a saved job.

        Steps:
        1. Validate ownership of resume version and job.
        2. Check for cached match (idempotency).
        3. Parse the job description with JobDescriptionAnalyzer.
        4. Look up or compute ATS analysis.
        5. Compute match sub-scores and overall score.
        6. Generate fit summary, strengths, weaknesses, improvement actions.
        7. Persist and return JobMatch.
        """
        # --- 1. Validate resume version ---
        resume_version = await self._get_resume_version(user_id, resume_version_id)

        # --- 2. Validate job ---
        job = await self._get_job(user_id, job_id)

        # --- 3. Check for cached match (idempotent) ---
        cached = await self._get_cached_match(user_id, job_id, resume_version_id)
        if cached:
            return cached

        # --- 4. Analyze job description ---
        jd_analysis = JobDescriptionAnalyzer.analyze(job.description)

        # --- 5. Look up or compute ATS analysis ---
        ats_analysis = await self._get_or_create_ats(user_id, resume_version_id, job.description)

        # --- 6. Compute sub-scores ---
        scores = self._compute_scores(resume_version, jd_analysis, ats_analysis)

        # --- 7. Persist ---
        job_match = JobMatch(
            user_id=user_id,
            resume_version_id=resume_version_id,
            job_id=job_id,
            overall_match_score=scores["overall_match_score"],
            skills_match_score=scores["skills_match_score"],
            experience_match_score=scores["experience_match_score"],
            education_match_score=scores["education_match_score"],
            keyword_match_score=scores["keyword_match_score"],
            matched_skills=scores["matched_skills"],
            missing_skills=scores["missing_skills"],
            strengths=scores["strengths"],
            weaknesses=scores["weaknesses"],
            fit_summary=scores["fit_summary"],
            improvement_actions=scores["improvement_actions"],
        )

        try:
            self.db.add(job_match)
            await self.db.commit()
            await self.db.refresh(job_match)
        except Exception as e:
            logger.error(
                f"Failed to save job match for user={user_id}, job={job_id}, version={resume_version_id}: {str(e)}",
                exc_info=True,
            )
            await self.db.rollback()
            raise HTTPException(status_code=500, detail="Failed to save job match result.")

        return job_match

    async def list_matches(self, user_id: uuid.UUID) -> list[JobMatch]:
        """List all job matches for the authenticated user, newest first."""
        stmt = (
            select(JobMatch)
            .where(JobMatch.user_id == user_id)
            .order_by(JobMatch.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_match(self, user_id: uuid.UUID, match_id: uuid.UUID) -> JobMatch:
        """Get a single job match by ID. Ownership enforced."""
        stmt = select(JobMatch).where(
            JobMatch.id == match_id,
            JobMatch.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        match = result.scalar_one_or_none()
        if not match:
            raise HTTPException(status_code=404, detail="Job match not found")
        return match

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    async def _get_resume_version(self, user_id: uuid.UUID, version_id: uuid.UUID) -> ResumeVersion:
        """Fetch resume version with ownership and soft-delete checks."""
        stmt = (
            select(ResumeVersion)
            .join(ResumeProfile, ResumeVersion.profile_id == ResumeProfile.id)
            .where(
                ResumeVersion.id == version_id,
                ResumeVersion.user_id == user_id,
                ResumeVersion.is_deleted == False,
                ResumeProfile.is_deleted == False,
            )
        )
        result = await self.db.execute(stmt)
        version = result.scalar_one_or_none()
        if not version:
            raise HTTPException(status_code=404, detail="Resume version not found")
        if version.contact_info is None:
            raise HTTPException(
                status_code=400,
                detail="Resume version has not been parsed yet. Please run parse first.",
            )
        return version

    async def _get_job(self, user_id: uuid.UUID, job_id: uuid.UUID) -> Job:
        """Fetch job with ownership and soft-delete checks."""
        stmt = select(Job).where(
            Job.id == job_id,
            Job.user_id == user_id,
            Job.is_deleted == False,
        )
        result = await self.db.execute(stmt)
        job = result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job

    async def _get_cached_match(
        self, user_id: uuid.UUID, job_id: uuid.UUID, version_id: uuid.UUID
    ) -> JobMatch | None:
        """Return an existing match for the same user/job/version triple if one exists."""
        stmt = select(JobMatch).where(
            JobMatch.user_id == user_id,
            JobMatch.job_id == job_id,
            JobMatch.resume_version_id == version_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_or_create_ats(
        self, user_id: uuid.UUID, version_id: uuid.UUID, job_description: str
    ) -> ATSAnalysis | None:
        """Look up a cached ATS analysis or create one on-the-fly."""
        jd_clean = job_description.strip()
        jd_hash = hashlib.sha256(jd_clean.encode("utf-8")).hexdigest()

        stmt = select(ATSAnalysis).where(
            ATSAnalysis.resume_version_id == version_id,
            ATSAnalysis.job_description_hash == jd_hash,
        )
        result = await self.db.execute(stmt)
        cached = result.scalar_one_or_none()
        if cached:
            return cached

        # Create a lightweight ATS analysis for this match
        from app.resumes.service import ResumeStorageService
        version_service = ResumeVersionService(self.db, ResumeStorageService())
        try:
            return await version_service.analyze_ats(user_id, version_id, job_description)
        except HTTPException:
            # If ATS analysis fails for some reason, continue without it
            logger.warning(f"ATS analysis unavailable for version {version_id}; proceeding with None.")
            return None

    @classmethod
    def _compute_scores(
        cls,
        resume_version: ResumeVersion,
        jd_analysis: dict,
        ats_analysis: ATSAnalysis | None,
    ) -> dict:
        """
        Deterministic scoring computation.

        Returns a dict with all JobMatch field values.
        """
        resume_text_lower = (resume_version.extracted_text or "").lower()

        # --- Skills Match ---
        resume_skills_set = {s.lower().strip() for s in (resume_version.skills or [])}
        required_skills = jd_analysis["required_skills"]
        preferred_skills = jd_analysis["preferred_skills"]

        matched_required = [
            s for s in required_skills
            if any(s.lower() in rs or rs in s.lower() for rs in resume_skills_set)
        ]
        matched_preferred = [
            s for s in preferred_skills
            if any(s.lower() in rs or rs in s.lower() for rs in resume_skills_set)
        ]

        required_pct = (len(matched_required) / len(required_skills) * 100) if required_skills else 100.0
        preferred_pct = (len(matched_preferred) / len(preferred_skills) * 100) if preferred_skills else 100.0
        skills_match_score = round(0.8 * required_pct + 0.2 * preferred_pct, 1)

        matched_skills_list = sorted(set(matched_required + matched_preferred))
        missing_skills_list = sorted(set(required_skills) - set(matched_required))

        # --- Experience Match ---
        jd_exp_years = jd_analysis["years_of_experience"]
        resume_exp_years = ResumeVersionService._estimate_experience_years(resume_version)

        if jd_exp_years == 0:
            experience_match_score = 100.0
        elif resume_exp_years >= jd_exp_years:
            experience_match_score = 100.0
        else:
            experience_match_score = round((resume_exp_years / jd_exp_years) * 100, 1)

        # --- Education Match ---
        jd_edu = jd_analysis["education_requirements"]
        jd_level = cls.EDU_LEVELS.get(jd_edu.lower(), 1)
        resume_level = ResumeVersionService._estimate_education_level(resume_version.education or [])

        if resume_level >= jd_level:
            education_match_score = 100.0
        else:
            education_match_score = round((resume_level / jd_level) * 100, 1) if jd_level > 0 else 100.0

        # --- Keyword Match ---
        jd_keywords = jd_analysis["keywords"]
        matched_keywords = [
            kw for kw in jd_keywords
            if re.search(rf"\b{re.escape(kw)}\b", resume_text_lower)
        ]
        keyword_match_score = round((len(matched_keywords) / len(jd_keywords) * 100), 1) if jd_keywords else 100.0

        # --- ATS Score Contribution ---
        ats_score_value = 0.0
        if ats_analysis:
            ats_score_value = float(ats_analysis.ats_score)
        else:
            # Fallback: compute inline using the same deterministic logic
            ats_fallback = ATSScoringService.score(resume_version, jd_analysis)
            ats_score_value = float(ats_fallback["ats_score"])

        # --- Overall Weighted Score ---
        overall_match_score = round(
            cls.WEIGHT_SKILLS * skills_match_score
            + cls.WEIGHT_EXPERIENCE * experience_match_score
            + cls.WEIGHT_EDUCATION * education_match_score
            + cls.WEIGHT_KEYWORDS * keyword_match_score
            + cls.WEIGHT_ATS * ats_score_value,
            1,
        )

        # --- Strengths ---
        strengths = []
        if skills_match_score >= 80:
            strengths.append(f"Strong skills alignment — {len(matched_required)}/{len(required_skills)} required skills matched.")
        if experience_match_score == 100 and jd_exp_years > 0:
            strengths.append(f"Meets or exceeds the required {jd_exp_years} years of experience.")
        elif experience_match_score == 100 and jd_exp_years == 0:
            strengths.append("No specific experience requirement for this role.")
        if education_match_score == 100:
            strengths.append(f"Education level meets the {jd_edu} requirement.")
        if keyword_match_score >= 80:
            strengths.append(f"Excellent keyword coverage — {len(matched_keywords)}/{len(jd_keywords)} keywords found.")
        if overall_match_score >= 80:
            strengths.append("Overall profile is a strong fit for this position.")
        if not strengths:
            strengths.append("Resume contains foundational qualifications for this role.")

        # --- Weaknesses ---
        weaknesses = []
        if skills_match_score < 60:
            weaknesses.append(f"Low skills overlap — only {len(matched_required)}/{len(required_skills)} required skills found.")
        if experience_match_score < 100 and jd_exp_years > 0:
            weaknesses.append(f"Experience gap — resume shows ~{resume_exp_years} years vs. required {jd_exp_years} years.")
        if education_match_score < 100:
            weaknesses.append(f"Education level does not fully meet the {jd_edu} requirement.")
        if keyword_match_score < 50:
            weaknesses.append("Significant keyword gaps reduce ATS pass-through probability.")
        if missing_skills_list:
            top_missing = ", ".join(missing_skills_list[:5])
            weaknesses.append(f"Missing critical required skills: {top_missing}.")
        if not weaknesses:
            weaknesses.append("No significant weaknesses identified.")

        # --- Fit Summary ---
        if overall_match_score >= 85:
            fit_label = "Excellent Fit"
            fit_desc = "Your resume closely aligns with this role's requirements."
        elif overall_match_score >= 70:
            fit_label = "Good Fit"
            fit_desc = "Your profile matches most key requirements with minor gaps."
        elif overall_match_score >= 50:
            fit_label = "Moderate Fit"
            fit_desc = "Several qualification gaps exist but the foundation is present."
        else:
            fit_label = "Low Fit"
            fit_desc = "Significant gaps between your resume and this role's requirements."

        fit_summary = (
            f"{fit_label} ({overall_match_score}/100). {fit_desc} "
            f"Skills: {skills_match_score}%, Experience: {experience_match_score}%, "
            f"Education: {education_match_score}%, Keywords: {keyword_match_score}%."
        )

        # --- Improvement Actions ---
        improvement_actions = []
        if missing_skills_list:
            top = ", ".join(missing_skills_list[:5])
            improvement_actions.append(f"Add or highlight these missing required skills: {top}.")
        if experience_match_score < 100 and jd_exp_years > 0:
            improvement_actions.append(
                f"Strengthen your experience section to demonstrate {jd_exp_years}+ years of relevant work."
            )
        if education_match_score < 100:
            improvement_actions.append(
                f"If applicable, highlight your {jd_edu}-level education or equivalent qualifications."
            )
        if keyword_match_score < 70:
            missing_kw = [kw for kw in jd_keywords if kw not in [k.lower() for k in matched_keywords]]
            top_kw = ", ".join(missing_kw[:5])
            improvement_actions.append(f"Incorporate these keywords into your resume: {top_kw}.")
        jd_certs = jd_analysis.get("certifications", [])
        if jd_certs:
            resume_certs_lower = [c.lower() for c in (resume_version.certifications or [])]
            missing_certs = [c for c in jd_certs if c.lower() not in resume_certs_lower]
            if missing_certs:
                improvement_actions.append(
                    f"Consider obtaining these certifications: {', '.join(missing_certs)}."
                )
        if not improvement_actions:
            improvement_actions.append("Your resume is well-aligned. Consider tailoring your summary for this specific role.")

        return {
            "overall_match_score": overall_match_score,
            "skills_match_score": skills_match_score,
            "experience_match_score": experience_match_score,
            "education_match_score": education_match_score,
            "keyword_match_score": keyword_match_score,
            "matched_skills": matched_skills_list,
            "missing_skills": missing_skills_list,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "fit_summary": fit_summary,
            "improvement_actions": improvement_actions,
        }
