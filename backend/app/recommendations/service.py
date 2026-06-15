"""Recommendations module — service layer. Sprint 10 Feedback Learning Loop."""
import logging
import uuid
from datetime import datetime, timezone, timedelta
from collections import Counter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.recommendations.models import RecommendationSignal
from app.applications.models import JobApplication, OutcomeType
from app.jobs.models import Job, JobMatch, SkillGapAnalysis
from app.resumes.models import ResumeVersion
from app.roadmap.models import CareerRoadmap, RoadmapMilestone

logger = logging.getLogger(__name__)


class FeedbackService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_signals(self, user_id: uuid.UUID) -> dict:
        """
        Processes applications and milestones to generate new recommendation signals.
        Enforces idempotency, soft-delete protection, and transaction safety.
        """
        now = datetime.now(timezone.utc)

        # 1. Fetch existing signals to prevent duplicates
        stmt_sig = select(RecommendationSignal).where(RecommendationSignal.user_id == user_id)
        res_sig = await self.db.execute(stmt_sig)
        existing_signals = list(res_sig.scalars().all())

        existing_keys = set()
        for s in existing_signals:
            if s.application_id:
                existing_keys.add((s.signal_type, s.application_id))
            if s.job_match_id:
                existing_keys.add((s.signal_type, s.job_match_id))
            if s.signal_type == "roadmap_completed":
                title = s.metadata_.get("milestone_title")
                if title:
                    existing_keys.add((s.signal_type, title))

        # 2. Fetch active applications (soft-delete protection)
        stmt_apps = (
            select(JobApplication, JobMatch, ResumeVersion, Job)
            .join(Job, JobApplication.job_id == Job.id)
            .join(ResumeVersion, JobApplication.resume_version_id == ResumeVersion.id)
            .outerjoin(
                JobMatch,
                (JobApplication.job_id == JobMatch.job_id) &
                (JobApplication.resume_version_id == JobMatch.resume_version_id) &
                (JobApplication.user_id == JobMatch.user_id)
            )
            .where(
                JobApplication.user_id == user_id,
                Job.is_deleted == False,
                ResumeVersion.is_deleted == False
            )
        )
        res_apps = await self.db.execute(stmt_apps)
        rows = res_apps.all()

        proposed_signals = []

        # 3. Scan applications for outcomes
        for app, match, version, job in rows:
            status = app.status.lower().strip()

            # Success / interview / offer indicators
            is_interview = (
                app.interview_at is not None or
                status in ("interview", "offer") or
                app.outcome_type in (OutcomeType.interviewed, OutcomeType.offered, OutcomeType.accepted)
            )
            is_offer = (
                app.offer_at is not None or
                status == "offer" or
                app.outcome_type in (OutcomeType.offered, OutcomeType.accepted)
            )
            is_acceptance = app.outcome_type == OutcomeType.accepted
            is_rejection = (
                app.rejection_at is not None or
                status == "rejected" or
                app.outcome_type == OutcomeType.rejected
            )
            is_no_response = (
                status == "applied" and
                app.applied_at is not None and
                (now - app.applied_at) > timedelta(days=14)
            )

            # Map to signal definitions
            app_metadata = {"job_title": job.title if job else None, "company": job.company if job else None}

            if is_acceptance:
                proposed_signals.append(RecommendationSignal(
                    user_id=user_id,
                    application_id=app.id,
                    resume_version_id=version.id,
                    job_match_id=match.id if match else None,
                    signal_type="acceptance_received",
                    signal_source="application",
                    signal_value=3.0,
                    confidence_score=1.0,
                    signal_weight=3.0 * 1.0,
                    metadata_=app_metadata
                ))
            elif is_offer:
                proposed_signals.append(RecommendationSignal(
                    user_id=user_id,
                    application_id=app.id,
                    resume_version_id=version.id,
                    job_match_id=match.id if match else None,
                    signal_type="offer_received",
                    signal_source="application",
                    signal_value=2.0,
                    confidence_score=0.95,
                    signal_weight=2.0 * 0.95,
                    metadata_=app_metadata
                ))
            elif is_interview:
                proposed_signals.append(RecommendationSignal(
                    user_id=user_id,
                    application_id=app.id,
                    resume_version_id=version.id,
                    job_match_id=match.id if match else None,
                    signal_type="interview_received",
                    signal_source="application",
                    signal_value=1.0,
                    confidence_score=0.90,
                    signal_weight=1.0 * 0.90,
                    metadata_=app_metadata
                ))

            if is_rejection:
                proposed_signals.append(RecommendationSignal(
                    user_id=user_id,
                    application_id=app.id,
                    resume_version_id=version.id,
                    job_match_id=match.id if match else None,
                    signal_type="rejection_received",
                    signal_source="application",
                    signal_value=-1.0,
                    confidence_score=0.80,
                    signal_weight=-1.0 * 0.80,
                    metadata_=app_metadata
                ))

            if is_no_response:
                proposed_signals.append(RecommendationSignal(
                    user_id=user_id,
                    application_id=app.id,
                    resume_version_id=version.id,
                    job_match_id=match.id if match else None,
                    signal_type="no_response",
                    signal_source="application",
                    signal_value=-0.5,
                    confidence_score=0.70,
                    signal_weight=-0.5 * 0.70,
                    metadata_={"applied_at": app.applied_at.isoformat()}
                ))

            # Match success / failure
            if match:
                if match.overall_match_score >= 80.0 and (is_interview or is_offer or is_acceptance):
                    proposed_signals.append(RecommendationSignal(
                        user_id=user_id,
                        application_id=app.id,
                        resume_version_id=version.id,
                        job_match_id=match.id,
                        signal_type="high_match_success",
                        signal_source="job_match",
                        signal_value=1.5,
                        confidence_score=0.85,
                        signal_weight=1.5 * 0.85,
                        metadata_={"match_score": match.overall_match_score}
                    ))
                elif match.overall_match_score < 60.0 and is_rejection:
                    proposed_signals.append(RecommendationSignal(
                        user_id=user_id,
                        application_id=app.id,
                        resume_version_id=version.id,
                        job_match_id=match.id,
                        signal_type="low_match_failure",
                        signal_source="job_match",
                        signal_value=-1.0,
                        confidence_score=0.80,
                        signal_weight=-1.0 * 0.80,
                        metadata_={"match_score": match.overall_match_score}
                    ))

        # 4. Scan roadmap completed milestones
        stmt_m = (
            select(RoadmapMilestone)
            .join(CareerRoadmap, RoadmapMilestone.roadmap_id == CareerRoadmap.id)
            .where(
                CareerRoadmap.user_id == user_id,
                RoadmapMilestone.completion_status == "completed"
            )
        )
        res_m = await self.db.execute(stmt_m)
        milestones = list(res_m.scalars().all())

        for m in milestones:
            proposed_signals.append(RecommendationSignal(
                user_id=user_id,
                application_id=None,
                resume_version_id=None,
                job_match_id=None,
                signal_type="roadmap_completed",
                signal_source="roadmap",
                signal_value=0.5,
                confidence_score=0.90,
                signal_weight=0.5 * 0.90,
                metadata_={"milestone_title": m.milestone_title, "skill_gap_id": str(m.skill_gap_id) if m.skill_gap_id else None}
            ))

        # 5. Filter duplicates (idempotency)
        to_insert = []
        generated_count = 0
        skipped_count = 0

        for sig in proposed_signals:
            is_dup = False
            if sig.application_id and (sig.signal_type, sig.application_id) in existing_keys:
                is_dup = True
            elif sig.job_match_id and (sig.signal_type, sig.job_match_id) in existing_keys:
                is_dup = True
            elif sig.signal_type == "roadmap_completed":
                title = sig.metadata_.get("milestone_title")
                if title and (sig.signal_type, title) in existing_keys:
                    is_dup = True

            if is_dup:
                skipped_count += 1
            else:
                to_insert.append(sig)
                generated_count += 1

                # Track key locally to prevent duplicates within the same batch
                if sig.application_id:
                    existing_keys.add((sig.signal_type, sig.application_id))
                if sig.job_match_id:
                    existing_keys.add((sig.signal_type, sig.job_match_id))
                if sig.signal_type == "roadmap_completed":
                    title = sig.metadata_.get("milestone_title")
                    if title:
                        existing_keys.add((sig.signal_type, title))

        # 6. Save (transaction safety)
        if to_insert:
            try:
                for sig in to_insert:
                    self.db.add(sig)
                await self.db.commit()
            except Exception as e:
                logger.error(f"Failed to save recommendation signals: {str(e)}", exc_info=True)
                await self.db.rollback()
                raise HTTPException(status_code=500, detail="Failed to save recommendation signals.")

        return {
            "generated_count": generated_count,
            "skipped_count": skipped_count
        }

    async def get_signals(self, user_id: uuid.UUID) -> list[RecommendationSignal]:
        """Returns all recommendation signals for the user, ordered by creation date descending."""
        stmt = (
            select(RecommendationSignal)
            .where(RecommendationSignal.user_id == user_id)
            .order_by(RecommendationSignal.created_at.desc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_summary(self, user_id: uuid.UUID) -> dict:
        """
        Aggregates learning feedback to generate a summary of best-performing
        resumes, converting job categories, and success/rejection-correlated skills.
        """
        # Fetch active applications
        stmt_apps = (
            select(JobApplication, ResumeVersion)
            .join(Job, JobApplication.job_id == Job.id)
            .join(ResumeVersion, JobApplication.resume_version_id == ResumeVersion.id)
            .where(
                JobApplication.user_id == user_id,
                Job.is_deleted == False,
                ResumeVersion.is_deleted == False
            )
        )
        res_apps = await self.db.execute(stmt_apps)
        rows = res_apps.all()

        # Fetch signals
        stmt_sig = select(RecommendationSignal).where(RecommendationSignal.user_id == user_id)
        res_sig = await self.db.execute(stmt_sig)
        signals = list(res_sig.scalars().all())

        # Group signals by type
        signal_counts = {}
        for s in signals:
            signal_counts[s.signal_type] = signal_counts.get(s.signal_type, 0) + 1

        # Track outcomes
        interview_versions = set()
        offer_versions = set()
        rejection_versions = set()

        for s in signals:
            if s.signal_type in ("interview_received", "offer_received", "acceptance_received", "high_match_success"):
                if s.resume_version_id:
                    interview_versions.add(s.resume_version_id)
            if s.signal_type in ("offer_received", "acceptance_received"):
                if s.resume_version_id:
                    offer_versions.add(s.resume_version_id)
            if s.signal_type in ("rejection_received", "low_match_failure"):
                if s.resume_version_id:
                    rejection_versions.add(s.resume_version_id)

        # Skill performance counters
        skills_success_counter = Counter()
        skills_rejection_counter = Counter()

        # Resume mapping setup
        resume_stats = {}  # {version_id: {"version_number", "filename", "sent": 0, "interviews": 0}}
        job_category_stats = {}  # {(company, title): {"sent": 0, "interviews": 0}}

        for app, version in rows:
            v_id = version.id
            if v_id not in resume_stats:
                resume_stats[v_id] = {
                    "id": v_id,
                    "version_number": version.version_number,
                    "filename": version.original_filename,
                    "applications_sent": 0,
                    "interviews": 0
                }

            status = app.status.lower().strip()
            is_sent = status not in ("draft", "saved")
            is_int = (
                app.interview_at is not None or
                status in ("interview", "offer") or
                app.outcome_type in (OutcomeType.interviewed, OutcomeType.offered, OutcomeType.accepted)
            )

            job = app.job_snapshot or {}
            job_key = (job.get("company"), job.get("title"))
            if job_key not in job_category_stats:
                job_category_stats[job_key] = {"sent": 0, "interviews": 0}

            if is_sent:
                resume_stats[v_id]["applications_sent"] += 1
                job_category_stats[job_key]["sent"] += 1
                if is_int:
                    resume_stats[v_id]["interviews"] += 1
                    job_category_stats[job_key]["interviews"] += 1

            # Skill mapping
            v_skills = version.skills or []
            skills_set = {s.lower().strip() for s in v_skills if isinstance(s, str)}

            if v_id in interview_versions or v_id in offer_versions:
                for sk in skills_set:
                    skills_success_counter[sk] += 1
            if v_id in rejection_versions:
                for sk in skills_set:
                    skills_rejection_counter[sk] += 1

        # Format outputs
        skills_success = [{"skill": k, "score": float(v)} for k, v in skills_success_counter.most_common(5)]
        skills_rejection = [{"skill": k, "score": float(v)} for k, v in skills_rejection_counter.most_common(5)]

        best_performing_resumes = []
        for r_stat in resume_stats.values():
            sent = r_stat["applications_sent"]
            r_stat["interview_rate"] = r_stat["interviews"] / sent if sent > 0 else 0.0
            best_performing_resumes.append(r_stat)
        best_performing_resumes.sort(key=lambda x: (x["interview_rate"], x["applications_sent"]), reverse=True)
        best_performing_resumes = best_performing_resumes[:5]

        highest_converting_categories = []
        for (company, title), stats in job_category_stats.items():
            sent = stats["sent"]
            rate = stats["interviews"] / sent if sent > 0 else 0.0
            highest_converting_categories.append({
                "company": company,
                "title": title,
                "interview_rate": rate,
                "applications_sent": sent
            })
        highest_converting_categories.sort(key=lambda x: (x["interview_rate"], x["applications_sent"]), reverse=True)
        highest_converting_categories = highest_converting_categories[:5]

        return {
            "skills_success": skills_success,
            "skills_rejection": skills_rejection,
            "best_performing_resumes": best_performing_resumes,
            "highest_converting_categories": highest_converting_categories,
            "signal_counts_by_type": signal_counts
        }
