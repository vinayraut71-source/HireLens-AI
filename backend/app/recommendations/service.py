import logging
import uuid
import hashlib
from datetime import datetime, timezone, timedelta
from collections import Counter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, desc, and_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from app.recommendations.models import RecommendationSignal, JobRecommendation
from app.applications.models import JobApplication, OutcomeType
from app.jobs.models import Job, JobMatch, SkillGapAnalysis, SkillGap, MatchResult
from app.resumes.models import ResumeProfile, ResumeVersion, ATSAnalysis
from app.roadmap.models import CareerRoadmap, RoadmapMilestone
from app.analytics.models import AnalyticsSnapshot

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


class JobDiscoveryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def discover_jobs(self, user_id: uuid.UUID) -> list[JobRecommendation]:
        """
        Intelligent Job Discovery Agent recommendation generator.
        Generates/overwrites recommendations score deterministically.
        """
        # 1. Fetch user's active resume version (default profile's active version first, fallback to latest)
        stmt = (
            select(ResumeVersion)
            .join(ResumeProfile, ResumeVersion.profile_id == ResumeProfile.id)
            .where(
                ResumeProfile.user_id == user_id,
                ResumeProfile.is_default == True,
                ResumeVersion.is_deleted == False
            )
            .order_by(ResumeVersion.version_number.desc())
            .limit(1)
        )
        res = await self.db.execute(stmt)
        resume_version = res.scalar_one_or_none()
        if not resume_version:
            stmt_fb = (
                select(ResumeVersion)
                .where(
                    ResumeVersion.user_id == user_id,
                    ResumeVersion.is_deleted == False
                )
                .order_by(ResumeVersion.created_at.desc())
                .limit(1)
            )
            res_fb = await self.db.execute(stmt_fb)
            resume_version = res_fb.scalar_one_or_none()

        if not resume_version:
            raise HTTPException(status_code=404, detail="No active resume version found for user")

        # 2. Fetch active non-deleted jobs in the system (global selection candidates)
        jobs_stmt = select(Job).where(Job.is_deleted == False, Job.job_status == "active")
        jobs_res = await self.db.execute(jobs_stmt)
        jobs = jobs_res.scalars().all()

        # Pre-fetch elements for user feedback score calculation
        sig_stmt = select(RecommendationSignal).where(RecommendationSignal.user_id == user_id)
        sig_res = await self.db.execute(sig_stmt)
        all_signals = list(sig_res.scalars().all())

        # Pre-fetch latest Analytics Snapshot
        snap_stmt = (
            select(AnalyticsSnapshot)
            .where(AnalyticsSnapshot.user_id == user_id)
            .order_by(AnalyticsSnapshot.generated_at.desc())
            .limit(1)
        )
        snap_res = await self.db.execute(snap_stmt)
        snapshot = snap_res.scalar_one_or_none()

        # Fetch successful applications for analytics score mapping (interview, offer, or accepted)
        success_stmt = (
            select(Job.company, Job.title)
            .join(JobApplication, Job.id == JobApplication.job_id)
            .where(
                JobApplication.user_id == user_id,
                JobApplication.status.in_(["interview", "offer", "accepted"]),
                Job.is_deleted == False
            )
        )
        success_res = await self.db.execute(success_stmt)
        success_jobs = list(success_res.all())

        # For checking SkillGap table status later
        sg_table_stmt = select(SkillGap).where(SkillGap.user_id == user_id, SkillGap.status == "completed")
        sg_table_res = await self.db.execute(sg_table_stmt)
        completed_sg_names = {sg.skill_name.lower().strip() for sg in sg_table_res.scalars().all()}

        recommendations_list = []

        for job in jobs:
            # --- 1. Match Score (30%) ---
            match_score = 0.0
            job_match_stmt = select(JobMatch).where(
                JobMatch.user_id == user_id,
                JobMatch.job_id == job.id,
                JobMatch.resume_version_id == resume_version.id
            )
            job_match_res = await self.db.execute(job_match_stmt)
            job_match = job_match_res.scalar_one_or_none()

            if job_match:
                match_score = job_match.overall_match_score
            else:
                match_res_stmt = select(MatchResult).where(
                    MatchResult.user_id == user_id,
                    MatchResult.job_id == job.id,
                    MatchResult.version_id == resume_version.id
                )
                match_res = (await self.db.execute(match_res_stmt)).scalar_one_or_none()
                if match_res:
                    match_score = match_res.overall_score if match_res.overall_score > 1.0 else match_res.overall_score * 100.0

            # --- 2. ATS Score (25%) ---
            ats_score = 0.0
            jd_clean = job.description.strip()
            jd_hash = hashlib.sha256(jd_clean.encode("utf-8")).hexdigest()

            ats_stmt = (
                select(ATSAnalysis.ats_score)
                .join(ResumeVersion, ATSAnalysis.resume_version_id == ResumeVersion.id)
                .where(
                    ResumeVersion.user_id == user_id,
                    ATSAnalysis.job_description_hash == jd_hash,
                    ResumeVersion.is_deleted == False
                )
            )
            ats_res = await self.db.execute(ats_stmt)
            ats_scores = list(ats_res.scalars().all())
            if ats_scores:
                ats_score = float(max(ats_scores))

            # --- 3. Feedback Score (20%) ---
            # Map signals belonging to this specific job match or application
            match_ids_stmt = select(JobMatch.id).where(JobMatch.user_id == user_id, JobMatch.job_id == job.id)
            match_ids = set((await self.db.execute(match_ids_stmt)).scalars().all())

            app_ids_stmt = select(JobApplication.id).where(JobApplication.user_id == user_id, JobApplication.job_id == job.id)
            app_ids = set((await self.db.execute(app_ids_stmt)).scalars().all())

            feedback_score = 50.0
            for s in all_signals:
                if s.job_match_id in match_ids or s.application_id in app_ids:
                    st = s.signal_type.lower().strip()
                    if st == "interview_received":
                        feedback_score += 15.0
                    elif st == "offer_received":
                        feedback_score += 25.0
                    elif st == "acceptance_received":
                        feedback_score += 30.0
                    elif st == "roadmap_completed":
                        feedback_score += 20.0
                    elif st == "rejection_received":
                        feedback_score -= 25.0
                    elif st == "no_response":
                        feedback_score -= 10.0
                    elif st == "low_match_failure":
                        feedback_score -= 15.0
            feedback_score = max(0.0, min(100.0, feedback_score))

            # --- 4. Skill Gap Score (15%) ---
            skill_gap_score = 100.0
            missing_skills_count = 0
            uncompleted_critical_count = 0
            progress_ratio = 0.0
            has_roadmap = False

            if job_match:
                missing_skills = job_match.missing_skills or []
                missing_skills_count = len(missing_skills)
                skill_gap_score -= (missing_skills_count * 10.0)
                skill_gap_score = max(40.0, skill_gap_score)

                sa_stmt = select(SkillGapAnalysis).where(SkillGapAnalysis.job_match_id == job_match.id)
                sa_res = await self.db.execute(sa_stmt)
                analyses = list(sa_res.scalars().all())

                rm_stmt = (
                    select(CareerRoadmap)
                    .options(selectinload(CareerRoadmap.milestones))
                    .where(CareerRoadmap.job_match_id == job_match.id)
                )
                rm_res = await self.db.execute(rm_stmt)
                roadmap = rm_res.scalar_one_or_none()

                completed_milestone_gap_ids = set()
                if roadmap:
                    has_roadmap = True
                    total_m = len(roadmap.milestones)
                    completed_m = sum(1 for m in roadmap.milestones if m.completion_status.lower() in ("completed", "done"))
                    progress_ratio = completed_m / total_m if total_m > 0 else 0.0

                    for m in roadmap.milestones:
                        if m.completion_status.lower() in ("completed", "done"):
                            completed_milestone_gap_ids.add(m.skill_gap_id)

                for analysis in analyses:
                    if analysis.learning_priority.lower() in ("critical", "high"):
                        is_completed = (
                            analysis.id in completed_milestone_gap_ids or
                            analysis.missing_skill.lower().strip() in completed_sg_names
                        )
                        if not is_completed:
                            uncompleted_critical_count += 1

                critical_penalty = min(30.0, uncompleted_critical_count * 15.0)
                skill_gap_score -= critical_penalty

                if has_roadmap:
                    skill_gap_score += (progress_ratio * 30.0)

            skill_gap_score = max(0.0, min(100.0, skill_gap_score))

            # --- 5. Analytics Success Signals (10%) ---
            analytics_score = 50.0
            company_matched = False
            title_matched = False

            if snapshot:
                if resume_version.id == snapshot.strongest_resume_version_id:
                    analytics_score += 20.0
                if (snapshot.interview_rate or 0.0) > 0.3:
                    analytics_score += 10.0
                if (snapshot.offer_rate or 0.0) > 0.1:
                    analytics_score += 10.0
                if (snapshot.acceptance_rate or 0.0) > 0.05:
                    analytics_score += 10.0

            for s_company, s_title in success_jobs:
                if s_company and job.company and s_company.strip().lower() == job.company.strip().lower():
                    company_matched = True
                if s_title and job.title and s_title.strip().lower() in job.title.strip().lower():
                    title_matched = True

            if company_matched:
                analytics_score += 15.0
            if title_matched:
                analytics_score += 15.0

            analytics_score = max(0.0, min(100.0, analytics_score))

            # --- Recommendation Score ---
            recommendation_score = (
                0.30 * match_score +
                0.25 * ats_score +
                0.20 * feedback_score +
                0.15 * skill_gap_score +
                0.10 * analytics_score
            )
            recommendation_score = round(recommendation_score, 2)

            # --- Structured Reasons ---
            recommendation_reason = {
                "high_match_score": match_score >= 80.0,
                "ats_compatible": ats_score >= 80.0,
                "skills_aligned": skill_gap_score >= 80.0,
                "similar_to_previous_success": feedback_score > 70.0 or company_matched or title_matched,
                "roadmap_progress_helpful": progress_ratio > 0.0
            }

            # --- Confidence Score ---
            ats_check_stmt = select(ATSAnalysis).where(
                ATSAnalysis.resume_version_id == resume_version.id,
                ATSAnalysis.job_description_hash == jd_hash
            )
            ats_check_res = await self.db.execute(ats_check_stmt)
            has_ats_analysis = ats_check_res.first() is not None

            confidence_score = 50.0
            if job_match is not None:
                confidence_score += 25.0
            if has_ats_analysis:
                confidence_score += 25.0

            # Delete old duplicate (idempotency safety)
            del_stmt = delete(JobRecommendation).where(
                JobRecommendation.user_id == user_id,
                JobRecommendation.job_id == job.id,
                JobRecommendation.resume_version_id == resume_version.id
            )
            await self.db.execute(del_stmt)

            job_snap = {
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "salary": f"${job.salary_min} - ${job.salary_max}" if (job.salary_min or job.salary_max) else None,
                "url": job.source_url
            }

            db_rec = JobRecommendation(
                user_id=user_id,
                job_id=job.id,
                resume_version_id=resume_version.id,
                recommendation_score=recommendation_score,
                match_score=match_score,
                ats_score=ats_score,
                skill_gap_score=skill_gap_score,
                feedback_score=feedback_score,
                confidence_score=confidence_score,
                recommendation_reason=recommendation_reason,
                recommendation_status="recommended",
                job_snapshot=job_snap
            )
            self.db.add(db_rec)
            recommendations_list.append(db_rec)

        try:
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

        # Query all recommendations ordered descending by score
        rec_stmt = (
            select(JobRecommendation)
            .join(Job, JobRecommendation.job_id == Job.id)
            .where(
                JobRecommendation.user_id == user_id,
                Job.is_deleted == False,
                Job.job_status == "active"
            )
            .order_by(desc(JobRecommendation.recommendation_score))
        )
        rec_res = await self.db.execute(rec_stmt)
        return list(rec_res.scalars().all())

    async def get_recommendations(self, user_id: uuid.UUID) -> list[JobRecommendation]:
        """
        Fetches recommendations. Uses cache if recommendations are < 24 hours old.
        """
        twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)
        stmt = (
            select(JobRecommendation)
            .join(Job, JobRecommendation.job_id == Job.id)
            .where(
                JobRecommendation.user_id == user_id,
                Job.is_deleted == False,
                Job.job_status == "active",
                JobRecommendation.created_at >= twenty_four_hours_ago
            )
            .order_by(desc(JobRecommendation.recommendation_score))
        )
        res = await self.db.execute(stmt)
        cached = list(res.scalars().all())
        if cached:
            return cached

        # Generate new
        return await self.discover_jobs(user_id)

    async def refresh_recommendations(self, user_id: uuid.UUID) -> list[JobRecommendation]:
        """
        Bypasses/purges cache and forces recalculation of recommendations.
        """
        stmt = delete(JobRecommendation).where(JobRecommendation.user_id == user_id)
        await self.db.execute(stmt)
        await self.db.commit()

        return await self.discover_jobs(user_id)

    async def update_recommendation_status(
        self, recommendation_id: uuid.UUID, user_id: uuid.UUID, status: str
    ) -> JobRecommendation:
        """
        Updates the status of a job recommendation for ownership validation.
        """
        stmt = select(JobRecommendation).where(
            JobRecommendation.id == recommendation_id,
            JobRecommendation.user_id == user_id
        )
        res = await self.db.execute(stmt)
        rec = res.scalar_one_or_none()
        if not rec:
            raise HTTPException(status_code=404, detail="Recommendation not found or ownership invalid")

        rec.recommendation_status = status
        rec.updated_at = datetime.now(timezone.utc)
        try:
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise
        return rec

    async def get_saved_recommendations(self, user_id: uuid.UUID) -> list[JobRecommendation]:
        """
        Fetches recommendations with status 'saved' for the user.
        """
        stmt = (
            select(JobRecommendation)
            .join(Job, JobRecommendation.job_id == Job.id)
            .where(
                JobRecommendation.user_id == user_id,
                Job.is_deleted == False,
                Job.job_status == "active",
                JobRecommendation.recommendation_status == "saved"
            )
            .order_by(desc(JobRecommendation.recommendation_score))
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())



