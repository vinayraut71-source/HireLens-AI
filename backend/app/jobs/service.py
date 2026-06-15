"""Jobs module — service layer. Sprint 5: Job CRUD + Intelligent Job Matching. Sprint 6: Skill Gap Intelligence."""
import re
import hashlib
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.jobs.models import Job, JobMatch, SkillGapAnalysis
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


class SkillGapService:
    """
    Sprint 6: Skill Gap Intelligence Engine.

    For each missing skill in a JobMatch, deterministically computes:
      - importance_score (0-100) based on JD frequency, ATS impact, match score impact
      - category (technical, soft-skill, certification, domain, tool)
      - learning_priority (critical, high, medium, low)
      - estimated_learning_time
      - recommendation_reason

    All scoring is deterministic. No Gemini / LLM calls.
    Results are idempotent (cached by job_match_id).
    """

    # Category classification keywords
    TECHNICAL_SKILLS = {
        "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust", "ruby", "php",
        "react", "angular", "vue", "next.js", "node.js", "express", "django", "fastapi", "flask",
        "spring boot", "dotnet", "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
        "html", "css", "graphql", "rest api", "machine learning", "deep learning", "nlp",
        "artificial intelligence", "data science", "pandas", "numpy", "tensorflow", "pytorch",
    }
    TOOL_SKILLS = {
        "docker", "kubernetes", "aws", "azure", "gcp", "git", "ci/cd", "jira", "linux",
    }
    CERT_SKILLS = {
        "aws certified", "pmp", "csm", "cissp", "ccna", "comptia", "itil", "certified scrummaster",
    }
    SOFT_SKILLS = {
        "agile", "scrum", "leadership", "communication", "teamwork", "problem solving",
    }

    # Learning time estimates by category
    LEARNING_TIMES = {
        "technical": {"critical": "3-6 months", "high": "2-4 months", "medium": "1-2 months", "low": "2-4 weeks"},
        "tool": {"critical": "2-4 months", "high": "1-3 months", "medium": "2-6 weeks", "low": "1-2 weeks"},
        "certification": {"critical": "2-4 months", "high": "1-3 months", "medium": "1-2 months", "low": "2-4 weeks"},
        "soft-skill": {"critical": "1-3 months", "high": "2-6 weeks", "medium": "1-4 weeks", "low": "1-2 weeks"},
        "domain": {"critical": "3-6 months", "high": "2-4 months", "medium": "1-2 months", "low": "2-4 weeks"},
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze_gaps(
        self, user_id: uuid.UUID, match_id: uuid.UUID
    ) -> list[SkillGapAnalysis]:
        """
        Generate skill gap analysis for a given job match.

        Steps:
        1. Validate match ownership.
        2. Check for cached gaps (idempotent).
        3. Fetch the job description and parse it.
        4. For each missing skill, compute importance, category, priority.
        5. Persist and return.
        """
        # --- 1. Validate match ownership ---
        job_match = await self._get_match(user_id, match_id)

        # --- 2. Check cache ---
        cached = await self._get_cached_gaps(match_id)
        if cached:
            return cached

        # --- 3. Get job description and analyze ---
        job = await self._get_job(user_id, job_match.job_id)
        jd_analysis = JobDescriptionAnalyzer.analyze(job.description)
        jd_text_lower = job.description.lower()

        # --- 4. Get ATS analysis for impact data ---
        ats_analysis = await self._get_ats_analysis(job_match.resume_version_id, job.description)

        # --- 5. Compute gaps for each missing skill ---
        missing_skills = job_match.missing_skills or []
        if not missing_skills:
            return []

        gap_records = []
        for skill in missing_skills:
            gap_data = self._compute_gap(
                skill=skill,
                jd_text_lower=jd_text_lower,
                jd_analysis=jd_analysis,
                ats_analysis=ats_analysis,
                job_match=job_match,
            )
            record = SkillGapAnalysis(
                user_id=user_id,
                resume_version_id=job_match.resume_version_id,
                job_match_id=match_id,
                missing_skill=skill,
                importance_score=gap_data["importance_score"],
                category=gap_data["category"],
                learning_priority=gap_data["learning_priority"],
                estimated_learning_time=gap_data["estimated_learning_time"],
                recommendation_reason=gap_data["recommendation_reason"],
                roadmap_priority_score=gap_data["roadmap_priority_score"],
            )
            gap_records.append(record)

        # Sort by roadmap_priority_score descending before persisting
        gap_records.sort(key=lambda g: g.roadmap_priority_score, reverse=True)

        # --- 6. Persist ---
        try:
            self.db.add_all(gap_records)
            await self.db.commit()
            for r in gap_records:
                await self.db.refresh(r)
        except Exception as e:
            logger.error(
                f"Failed to save skill gap analysis for match {match_id}: {str(e)}",
                exc_info=True,
            )
            await self.db.rollback()
            raise HTTPException(status_code=500, detail="Failed to save skill gap analysis.")

        return gap_records

    async def get_gaps(
        self, user_id: uuid.UUID, match_id: uuid.UUID
    ) -> list[SkillGapAnalysis]:
        """Retrieve skill gap analysis for a match. Ownership enforced."""
        await self._get_match(user_id, match_id)
        return await self._get_cached_gaps(match_id)

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    async def _get_match(self, user_id: uuid.UUID, match_id: uuid.UUID) -> JobMatch:
        """Fetch job match with ownership check."""
        stmt = select(JobMatch).where(
            JobMatch.id == match_id,
            JobMatch.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        match = result.scalar_one_or_none()
        if not match:
            raise HTTPException(status_code=404, detail="Job match not found")
        return match

    async def _get_job(self, user_id: uuid.UUID, job_id: uuid.UUID) -> Job:
        """Fetch job with ownership and soft-delete check."""
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

    async def _get_cached_gaps(self, match_id: uuid.UUID) -> list[SkillGapAnalysis]:
        """Return cached gap analysis for a match, ordered by roadmap_priority_score desc."""
        stmt = (
            select(SkillGapAnalysis)
            .where(SkillGapAnalysis.job_match_id == match_id)
            .order_by(SkillGapAnalysis.roadmap_priority_score.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _get_ats_analysis(
        self, version_id: uuid.UUID, job_description: str
    ) -> ATSAnalysis | None:
        """Look up cached ATS analysis for scoring context."""
        import hashlib
        jd_hash = hashlib.sha256(job_description.strip().encode("utf-8")).hexdigest()
        stmt = select(ATSAnalysis).where(
            ATSAnalysis.resume_version_id == version_id,
            ATSAnalysis.job_description_hash == jd_hash,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    def _classify_category(cls, skill: str) -> str:
        """Classify a skill into a category."""
        skill_lower = skill.lower().strip()
        if skill_lower in cls.CERT_SKILLS:
            return "certification"
        if skill_lower in cls.TOOL_SKILLS:
            return "tool"
        if skill_lower in cls.SOFT_SKILLS:
            return "soft-skill"
        if skill_lower in cls.TECHNICAL_SKILLS:
            return "technical"
        return "domain"

    @classmethod
    def _compute_gap(
        cls,
        skill: str,
        jd_text_lower: str,
        jd_analysis: dict,
        ats_analysis: ATSAnalysis | None,
        job_match: JobMatch,
    ) -> dict:
        """
        Deterministic computation for a single missing skill.

        importance_score = (jd_frequency_score * 0.4) + (ats_impact * 0.35) + (match_impact * 0.25)
        """
        skill_lower = skill.lower().strip()

        # --- JD Frequency Score (0-100) ---
        # Count occurrences of the skill in the job description
        occurrences = len(re.findall(rf"\b{re.escape(skill_lower)}\b", jd_text_lower))
        # Normalize: 1 mention = 30, 2 = 55, 3 = 75, 4+ = 90, in required section = +10
        if occurrences == 0:
            jd_freq_score = 20  # Still listed as required skill by analyzer
        elif occurrences == 1:
            jd_freq_score = 30
        elif occurrences == 2:
            jd_freq_score = 55
        elif occurrences == 3:
            jd_freq_score = 75
        else:
            jd_freq_score = 90

        # Boost if in required_skills list
        required_skills = [s.lower() for s in jd_analysis.get("required_skills", [])]
        if skill_lower in required_skills:
            jd_freq_score = min(100, jd_freq_score + 10)

        # --- ATS Impact Score (0-100) ---
        ats_impact = 50  # default
        if ats_analysis:
            missing_kw = [k.lower() for k in (ats_analysis.missing_keywords or [])]
            if skill_lower in missing_kw:
                ats_impact = 80  # This skill is a missing keyword in ATS
            missing_sk = [s.lower() for s in (ats_analysis.missing_skills or [])]
            if skill_lower in missing_sk:
                ats_impact = max(ats_impact, 85)  # Missing from ATS skill analysis

        # --- Match Score Impact (0-100) ---
        # How much would adding this skill improve the match score?
        total_required = len(jd_analysis.get("required_skills", []))
        if total_required > 0:
            # Each missing required skill reduces skills_match_score proportionally
            per_skill_impact = (100.0 / total_required) * 0.8  # 80% weight on required
            match_impact = min(100, round(per_skill_impact * 1.5))  # Amplify for significance
        else:
            match_impact = 30

        # --- Weighted Importance Score ---
        importance_score = round(
            0.40 * jd_freq_score + 0.35 * ats_impact + 0.25 * match_impact
        )
        importance_score = max(0, min(100, importance_score))

        # --- Category ---
        category = cls._classify_category(skill)

        # --- Learning Priority ---
        if importance_score >= 80:
            learning_priority = "critical"
        elif importance_score >= 60:
            learning_priority = "high"
        elif importance_score >= 40:
            learning_priority = "medium"
        else:
            learning_priority = "low"

        # --- Estimated Learning Time ---
        category_times = cls.LEARNING_TIMES.get(category, cls.LEARNING_TIMES["domain"])
        estimated_learning_time = category_times.get(learning_priority, "1-2 months")

        # --- Recommendation Reason ---
        reasons = []
        if skill_lower in required_skills:
            reasons.append(f"{skill} is listed as a required skill in the job description")
        if occurrences >= 2:
            reasons.append(f"mentioned {occurrences} times in the JD")
        if ats_analysis and skill_lower in [k.lower() for k in (ats_analysis.missing_keywords or [])]:
            reasons.append("flagged as a missing ATS keyword")
        if importance_score >= 70:
            reasons.append("has high impact on match score improvement")

        if reasons:
            recommendation_reason = f"{skill}: {'; '.join(reasons)}. Closing this gap would strengthen your candidacy."
        else:
            recommendation_reason = f"{skill}: Acquiring this skill would improve overall role alignment."

        # --- Learning Effort (Quantified for Roadmap score) ---
        priority_effort_map = {
            "critical": 80,
            "high": 60,
            "medium": 40,
            "low": 20
        }
        effort_score = priority_effort_map.get(learning_priority, 50)

        # --- Roadmap Priority Score (0-100) ---
        roadmap_priority_score = round(
            0.40 * ats_impact + 0.40 * match_impact + 0.20 * (100 - effort_score)
        )
        roadmap_priority_score = max(0, min(100, roadmap_priority_score))

        return {
            "importance_score": importance_score,
            "category": category,
            "learning_priority": learning_priority,
            "estimated_learning_time": estimated_learning_time,
            "recommendation_reason": recommendation_reason,
            "roadmap_priority_score": roadmap_priority_score,
        }
