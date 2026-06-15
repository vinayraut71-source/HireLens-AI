"""Analytics module — service layer. Sprint 9 Analytics Dashboard Foundation."""
import logging
import uuid
from datetime import datetime, timezone, timedelta
from collections import Counter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from fastapi import HTTPException

from app.analytics.models import AnalyticsSnapshot, AnalyticsInsight
from app.applications.models import JobApplication, OutcomeType
from app.jobs.models import Job, JobMatch, SkillGapAnalysis
from app.resumes.models import ResumeVersion

logger = logging.getLogger(__name__)


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_snapshot(self, user_id: uuid.UUID) -> tuple[AnalyticsSnapshot, list[AnalyticsInsight]]:
        """
        Generates an analytics snapshot with metrics, deltas, funnel stage counts, and insights.
        Enforces:
        - 1-hour caching / idempotency check.
        - Soft-delete protection.
        - Transaction safety.
        """
        now = datetime.now(timezone.utc)

        # 1. Cache Check (within last 1 hour)
        one_hour_ago = now - timedelta(hours=1)
        stmt_cache = (
            select(AnalyticsSnapshot)
            .where(AnalyticsSnapshot.user_id == user_id, AnalyticsSnapshot.generated_at >= one_hour_ago)
            .order_by(AnalyticsSnapshot.generated_at.desc())
        )
        res_cache = await self.db.execute(stmt_cache)
        cached_snap = res_cache.scalar_one_or_none()
        if cached_snap:
            stmt_insights = select(AnalyticsInsight).where(AnalyticsInsight.snapshot_id == cached_snap.id)
            res_insights = await self.db.execute(stmt_insights)
            return cached_snap, list(res_insights.scalars().all())

        # 2. Retrieve previous snapshot for delta calculation
        stmt_prev = (
            select(AnalyticsSnapshot)
            .where(AnalyticsSnapshot.user_id == user_id)
            .order_by(AnalyticsSnapshot.generated_at.desc())
            .limit(1)
        )
        res_prev = await self.db.execute(stmt_prev)
        prev_snap = res_prev.scalar_one_or_none()

        # 3. Retrieve all active applications (soft-delete protection)
        stmt_apps = (
            select(JobApplication, JobMatch, ResumeVersion)
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

        total_applications = len(rows)

        # Aggregation variables
        funnel_stage_counts = {
            "draft": 0, "saved": 0, "applied": 0, "in_review": 0,
            "assessment": 0, "interview": 0, "offer": 0, "rejected": 0, "withdrawn": 0
        }
        apps_sent = 0
        total_interviews = 0
        total_offers = 0
        total_rejections = 0
        total_acceptances = 0
        total_responses = 0

        match_scores = []
        app_version_stats = {}  # {version_id: {"sent": 0, "interviews": 0, "match_scores": [], "ats_score": None}}

        for app, match, version in rows:
            status = app.status.lower().strip()
            if status in funnel_stage_counts:
                funnel_stage_counts[status] += 1

            # Version mapping setup
            if version.id not in app_version_stats:
                app_version_stats[version.id] = {
                    "sent": 0,
                    "interviews": 0,
                    "match_scores": [],
                    "ats_score": version.ats_score,
                    "version_number": version.version_number,
                    "filename": version.original_filename
                }

            # Sent check
            is_sent = status not in ("draft", "saved")
            if is_sent:
                apps_sent += 1
                app_version_stats[version.id]["sent"] += 1

            # Interview check
            is_interview = (
                app.interview_at is not None or
                status in ("interview", "offer") or
                app.outcome_type in (OutcomeType.interviewed, OutcomeType.offered, OutcomeType.accepted)
            )
            if is_interview:
                total_interviews += 1
                if is_sent:
                    app_version_stats[version.id]["interviews"] += 1

            # Offer check
            is_offer = (
                app.offer_at is not None or
                status == "offer" or
                app.outcome_type in (OutcomeType.offered, OutcomeType.accepted)
            )
            if is_offer:
                total_offers += 1

            # Rejection check
            is_rejection = (
                app.rejection_at is not None or
                status == "rejected" or
                app.outcome_type == OutcomeType.rejected
            )
            if is_rejection:
                total_rejections += 1

            # Acceptance check
            if app.outcome_type == OutcomeType.accepted:
                total_acceptances += 1

            # Response check
            is_response = (
                app.first_response_at is not None or
                status not in ("draft", "saved", "applied")
            )
            if is_response and is_sent:
                total_responses += 1

            # Match Score collect
            if match and match.overall_match_score is not None:
                score_val = match.overall_match_score / 100.0
                match_scores.append(score_val)
                app_version_stats[version.id]["match_scores"].append(score_val)

        # Funnel rate calculations
        response_rate = total_responses / apps_sent if apps_sent > 0 else 0.0
        interview_rate = total_interviews / apps_sent if apps_sent > 0 else 0.0
        offer_rate = total_offers / apps_sent if apps_sent > 0 else 0.0
        acceptance_rate = total_acceptances / total_offers if total_offers > 0 else 0.0
        current_app_rate = apps_sent / total_applications if total_applications > 0 else 0.0

        # Averages
        average_match_score = sum(match_scores) / len(match_scores) if match_scores else 0.0

        # Retrieve all user's active resume versions for ATS averages
        stmt_versions = select(ResumeVersion).where(
            ResumeVersion.user_id == user_id, ResumeVersion.is_deleted == False
        )
        res_versions = await self.db.execute(stmt_versions)
        all_versions = list(res_versions.scalars().all())

        version_ats_scores = [v.ats_score for v in all_versions if v.ats_score is not None]
        average_ats_score = sum(version_ats_scores) / len(version_ats_scores) if version_ats_scores else 0.0

        # 4. Resume Intelligence (Strongest Resume version selection)
        strongest_resume_version_id = None
        if app_version_stats:
            # Rank versions by interview rate, tie break with average match score, ats score, newest
            ranked_versions = []
            for v_id, stats in app_version_stats.items():
                v_sent = stats["sent"]
                v_rate = stats["interviews"] / v_sent if v_sent > 0 else 0.0
                v_avg_match = sum(stats["match_scores"]) / len(stats["match_scores"]) if stats["match_scores"] else 0.0
                ranked_versions.append({
                    "id": v_id,
                    "rate": v_rate,
                    "avg_match": v_avg_match,
                    "ats": stats["ats_score"] or 0,
                    "version_num": stats["version_number"]
                })
            # Sort descending
            ranked_versions.sort(key=lambda x: (x["rate"], x["avg_match"], x["ats"], x["version_num"]), reverse=True)
            strongest_resume_version_id = ranked_versions[0]["id"]
        elif all_versions:
            # Fallback to highest ATS score
            all_versions.sort(key=lambda x: (x.ats_score or 0, x.version_number), reverse=True)
            strongest_resume_version_id = all_versions[0].id

        # 5. Delta calculations
        ats_score_delta = None
        match_score_delta = None
        application_rate_delta = None
        interview_rate_delta = None

        if prev_snap:
            ats_score_delta = average_ats_score - prev_snap.average_ats_score
            match_score_delta = average_match_score - prev_snap.average_match_score
            interview_rate_delta = interview_rate - prev_snap.interview_rate

            # Application rate delta calculation
            prev_funnel = prev_snap.funnel_stage_counts or {}
            prev_total = prev_snap.total_applications
            prev_sent = prev_total - prev_funnel.get("draft", 0) - prev_funnel.get("saved", 0)
            prev_app_rate = prev_sent / prev_total if prev_total > 0 else 0.0
            application_rate_delta = current_app_rate - prev_app_rate

        # 6. Build Snapshot Model
        snapshot = AnalyticsSnapshot(
            user_id=user_id,
            total_applications=total_applications,
            total_interviews=total_interviews,
            total_offers=total_offers,
            total_rejections=total_rejections,
            total_acceptances=total_acceptances,
            response_rate=response_rate,
            interview_rate=interview_rate,
            offer_rate=offer_rate,
            acceptance_rate=acceptance_rate,
            average_ats_score=average_ats_score,
            average_match_score=average_match_score,
            ats_score_delta=ats_score_delta,
            match_score_delta=match_score_delta,
            application_rate_delta=application_rate_delta,
            interview_rate_delta=interview_rate_delta,
            funnel_stage_counts=funnel_stage_counts,
            strongest_resume_version_id=strongest_resume_version_id,
            generated_at=now
        )

        # 7. Insights Generation
        insights_data = []

        # Insight 1: Resume Performance Comparison
        if len(app_version_stats) > 1:
            version_performances = []
            for v_id, stats in app_version_stats.items():
                v_sent = stats["sent"]
                if v_sent > 0:
                    v_rate = stats["interviews"] / v_sent
                    version_performances.append((stats["version_number"], v_rate))
            if len(version_performances) > 1:
                version_performances.sort(key=lambda x: x[1], reverse=True)
                best_v, best_r = version_performances[0]
                worst_v, worst_r = version_performances[-1]
                if best_r > worst_r:
                    insights_data.append(AnalyticsInsight(
                        insight_type="resume_comparison",
                        title="Resume Version Comparison",
                        description=f"Resume Version {best_v} performs better than Resume Version {worst_v} (interview rate: {best_r:.0%} vs {worst_r:.0%}).",
                        impact_score=max(5, int((best_r - worst_r) * 100))
                    ))

        # SkillGap data query for skill-based insights
        stmt_gaps = select(SkillGapAnalysis).where(SkillGapAnalysis.user_id == user_id)
        res_gaps = await self.db.execute(stmt_gaps)
        gaps = list(res_gaps.scalars().all())

        skill_counts = Counter([g.missing_skill for g in gaps])

        # Insight 2: Skill gap blocking matches
        if skill_counts:
            # Get matches count
            stmt_matches_count = select(func.count(JobMatch.id)).where(JobMatch.user_id == user_id)
            m_count = (await self.db.execute(stmt_matches_count)).scalar_one() or 0
            if m_count > 0:
                top_skill, top_count = skill_counts.most_common(1)[0]
                pct = top_count / m_count
                if pct >= 0.5:
                    insights_data.append(AnalyticsInsight(
                        insight_type="skill_gap",
                        title="Critical Skill Gap",
                        description=f"{top_skill} appears in {pct:.0%} of missed matches.",
                        impact_score=int(pct * 100)
                    ))

        # Insight 3: Skill impact correlation
        # Analyze if having a specific skill listed in the resume correlates to higher interview rates
        # Let's scan all user's resume versions' skills list
        skill_success_stats = {}  # {skill_name: {"with_sent": 0, "with_interviews": 0, "without_sent": 0, "without_interviews": 0}}
        for app, match, version in rows:
            is_sent = app.status.lower().strip() not in ("draft", "saved")
            is_int = (
                app.interview_at is not None or
                app.status.lower().strip() in ("interview", "offer") or
                app.outcome_type in (OutcomeType.interviewed, OutcomeType.offered, OutcomeType.accepted)
            )

            # Get skills list for version
            v_skills = version.skills or []
            # Normalize list of strings
            version_skills_set = {s.lower().strip() for s in v_skills if isinstance(s, str)}

            # Let's check a few critical skills or all skills in this application version
            for s in version_skills_set:
                if s not in skill_success_stats:
                    skill_success_stats[s] = {"w_sent": 0, "w_int": 0, "wo_sent": 0, "wo_int": 0}

            # Update stats
            for sk, stats in skill_success_stats.items():
                if sk in version_skills_set:
                    if is_sent:
                        stats["w_sent"] += 1
                        if is_int:
                            stats["w_int"] += 1
                else:
                    if is_sent:
                        stats["wo_sent"] += 1
                        if is_int:
                            stats["wo_int"] += 1

        correlated_skill = None
        correlation_diff = 0.0
        c_rate_with = 0.0
        c_rate_without = 0.0
        for sk, stats in skill_success_stats.items():
            if stats["w_sent"] >= 2 and stats["wo_sent"] >= 2:
                r_with = stats["w_int"] / stats["w_sent"]
                r_without = stats["wo_int"] / stats["wo_sent"]
                diff = r_with - r_without
                if diff > correlation_diff:
                    correlation_diff = diff
                    correlated_skill = sk
                    c_rate_with = r_with
                    c_rate_without = r_without

        if correlated_skill and correlation_diff > 0.1:
            insights_data.append(AnalyticsInsight(
                insight_type="skill_impact",
                title="Skill Impact on Interviews",
                description=f"Applications with {correlated_skill.upper()} skills have higher interview rates ({c_rate_with:.0%} vs {c_rate_without:.0%}).",
                impact_score=int(correlation_diff * 100)
            ))

        # Insight 4: ATS score performance
        if average_ats_score > 0:
            if average_ats_score < 75.0:
                insights_data.append(AnalyticsInsight(
                    insight_type="ats_warning",
                    title="ATS Score Warning",
                    description="Your average ATS score is below successful application averages. Focus on tailoring resume formatting and content.",
                    impact_score=50
                ))
            else:
                insights_data.append(AnalyticsInsight(
                    insight_type="ats_performance",
                    title="ATS Score Performance",
                    description="Your average ATS score is healthy. Keep tailoring your resumes to jobs to maintain strong scores.",
                    impact_score=15
                ))

        # Onboarding / Fallback Insights if we have less than 2 insights
        if len(insights_data) < 2:
            insights_data.append(AnalyticsInsight(
                insight_type="onboarding",
                title="Match to Saved Jobs",
                description="Match your resume to saved job descriptions to generate skill gaps and roadmaps.",
                impact_score=80
            ))
        if len(insights_data) < 3:
            insights_data.append(AnalyticsInsight(
                insight_type="onboarding",
                title="Track your First Application",
                description="Mark an application as 'Applied' to start tracking your interview rates.",
                impact_score=70
            ))

        # Assign snapshot_id to insights
        for insight in insights_data:
            insight.snapshot = snapshot

        # Transaction safety
        try:
            self.db.add(snapshot)
            for insight in insights_data:
                self.db.add(insight)
            await self.db.commit()
            await self.db.refresh(snapshot)
        except Exception as e:
            logger.error(f"Failed to generate and save analytics snapshot: {str(e)}", exc_info=True)
            await self.db.rollback()
            raise HTTPException(status_code=500, detail="Failed to generate analytics snapshot.")

        # Re-query insights to ensure they are loaded and not expired
        stmt_ins = select(AnalyticsInsight).where(AnalyticsInsight.snapshot_id == snapshot.id)
        res_ins = await self.db.execute(stmt_ins)
        insights_data = list(res_ins.scalars().all())

        return snapshot, insights_data

    async def get_latest_overview(self, user_id: uuid.UUID) -> dict:
        """
        Retrieves the latest analytics snapshot decorated with insights, resume intelligence and skill intelligence.
        Generates a new snapshot if none exists.
        """
        stmt = (
            select(AnalyticsSnapshot)
            .where(AnalyticsSnapshot.user_id == user_id)
            .order_by(AnalyticsSnapshot.generated_at.desc())
            .limit(1)
        )
        res = await self.db.execute(stmt)
        snapshot = res.scalar_one_or_none()

        if not snapshot:
            snapshot, insights = await self.generate_snapshot(user_id)
        else:
            stmt_insights = select(AnalyticsInsight).where(AnalyticsInsight.snapshot_id == snapshot.id)
            res_insights = await self.db.execute(stmt_insights)
            insights = list(res_insights.scalars().all())

        # Compute resume intelligence details dynamically
        resume_intelligence = await self._compute_resume_intelligence(user_id)

        # Compute skill intelligence details dynamically
        skill_intelligence = await self._compute_skill_intelligence(user_id)

        return {
            "snapshot": snapshot,
            "resume_intelligence": resume_intelligence,
            "skill_intelligence": skill_intelligence,
            "insights": insights
        }

    async def get_history(self, user_id: uuid.UUID) -> list[AnalyticsSnapshot]:
        """Returns snapshot history ordered by generated_at descending."""
        stmt = (
            select(AnalyticsSnapshot)
            .where(AnalyticsSnapshot.user_id == user_id)
            .order_by(AnalyticsSnapshot.generated_at.desc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_latest_insights(self, user_id: uuid.UUID) -> list[AnalyticsInsight]:
        """Returns insights for the latest snapshot."""
        stmt = (
            select(AnalyticsSnapshot)
            .where(AnalyticsSnapshot.user_id == user_id)
            .order_by(AnalyticsSnapshot.generated_at.desc())
            .limit(1)
        )
        res = await self.db.execute(stmt)
        snapshot = res.scalar_one_or_none()
        if not snapshot:
            snapshot, insights = await self.generate_snapshot(user_id)
            return insights

        stmt_insights = select(AnalyticsInsight).where(AnalyticsInsight.snapshot_id == snapshot.id)
        res_insights = await self.db.execute(stmt_insights)
        return list(res_insights.scalars().all())

    async def _compute_resume_intelligence(self, user_id: uuid.UUID) -> dict:
        """Helper to calculate best/worst/highest ATS/highest match resume versions."""
        # 1. Fetch all user versions
        stmt_v = select(ResumeVersion).where(ResumeVersion.user_id == user_id, ResumeVersion.is_deleted == False)
        res_v = await self.db.execute(stmt_v)
        versions = list(res_v.scalars().all())

        if not versions:
            return {
                "best_performing": None,
                "worst_performing": None,
                "highest_ats": None,
                "highest_match": None
            }

        # 2. Fetch all matches
        stmt_m = select(JobMatch).where(JobMatch.user_id == user_id)
        res_m = await self.db.execute(stmt_m)
        matches = list(res_m.scalars().all())

        # 3. Fetch applications
        stmt_apps = (
            select(JobApplication)
            .join(Job, JobApplication.job_id == Job.id)
            .join(ResumeVersion, JobApplication.resume_version_id == ResumeVersion.id)
            .where(
                JobApplication.user_id == user_id,
                Job.is_deleted == False,
                ResumeVersion.is_deleted == False
            )
        )
        res_apps = await self.db.execute(stmt_apps)
        apps = list(res_apps.scalars().all())

        # Highest ATS
        versions_with_ats = [v for v in versions if v.ats_score is not None]
        highest_ats_ver = max(versions_with_ats, key=lambda x: x.ats_score) if versions_with_ats else None

        # Highest Match
        highest_match_ver = None
        if matches:
            # Group matches by version
            version_match_scores = {}
            for match in matches:
                v_id = match.resume_version_id
                if v_id not in version_match_scores:
                    version_match_scores[v_id] = []
                version_match_scores[v_id].append(match.overall_match_score)

            best_v_id = None
            best_avg = -1.0
            for v_id, scs in version_match_scores.items():
                avg = sum(scs) / len(scs)
                if avg > best_avg:
                    best_avg = avg
                    best_v_id = v_id
            highest_match_ver = next((v for v in versions if v.id == best_v_id), None)

        if not highest_match_ver and highest_ats_ver:
            highest_match_ver = highest_ats_ver
        elif not highest_match_ver:
            highest_match_ver = versions[0]

        # Best / Worst Performing
        best_performing = None
        worst_performing = None

        version_app_stats = {}
        for app in apps:
            v_id = app.resume_version_id
            if v_id not in version_app_stats:
                version_app_stats[v_id] = {"sent": 0, "interviews": 0, "avg_match": 0.0}

            status = app.status.lower().strip()
            is_sent = status not in ("draft", "saved")
            is_int = (
                app.interview_at is not None or
                status in ("interview", "offer") or
                app.outcome_type in (OutcomeType.interviewed, OutcomeType.offered, OutcomeType.accepted)
            )
            if is_sent:
                version_app_stats[v_id]["sent"] += 1
                if is_int:
                    version_app_stats[v_id]["interviews"] += 1

        if version_app_stats:
            performances = []
            for v_id, stats in version_app_stats.items():
                sent = stats["sent"]
                rate = stats["interviews"] / sent if sent > 0 else 0.0
                v = next((x for x in versions if x.id == v_id), None)
                if v:
                    performances.append((v, rate, sent))

            # Best
            performances.sort(key=lambda x: (x[1], x[0].ats_score or 0, x[0].version_number), reverse=True)
            best_performing = performances[0][0]

            # Worst
            performances.sort(key=lambda x: (x[1], x[0].ats_score or 0, x[0].version_number))
            worst_performing = performances[0][0]

        if not best_performing:
            best_performing = highest_ats_ver or versions[0]
        if not worst_performing:
            worst_performing = highest_ats_ver or versions[0]

        def to_item(v):
            if not v:
                return None
            return {
                "id": v.id,
                "version_number": v.version_number,
                "original_filename": v.original_filename,
                "score": v.ats_score
            }

        return {
            "best_performing": to_item(best_performing),
            "worst_performing": to_item(worst_performing),
            "highest_ats": to_item(highest_ats_ver or versions[0]),
            "highest_match": to_item(highest_match_ver)
        }

    async def _compute_skill_intelligence(self, user_id: uuid.UUID) -> dict:
        """Helper to calculate skill gap lists and categories."""
        # Query SkillGapAnalysis
        stmt_gaps = select(SkillGapAnalysis).where(SkillGapAnalysis.user_id == user_id)
        res_gaps = await self.db.execute(stmt_gaps)
        gaps = list(res_gaps.scalars().all())

        # Top missing skills
        skill_counts = Counter([g.missing_skill for g in gaps])
        top_missing_skills = [{"skill": k, "count": v} for k, v in skill_counts.most_common(5)]

        # Gap categories
        cat_counts = Counter([g.category for g in gaps if g.category])
        most_frequent_gap_categories = [{"category": k, "count": v} for k, v in cat_counts.most_common(5)]

        # Highest impact skills
        skill_impact_scores = {}
        for g in gaps:
            if g.missing_skill not in skill_impact_scores:
                skill_impact_scores[g.missing_skill] = []
            skill_impact_scores[g.missing_skill].append(g.roadmap_priority_score)

        highest_impact_skills = []
        for sk, scs in skill_impact_scores.items():
            avg_impact = sum(scs) / len(scs)
            highest_impact_skills.append({"skill": sk, "score": avg_impact})
        highest_impact_skills.sort(key=lambda x: x["score"], reverse=True)
        highest_impact_skills = highest_impact_skills[:5]

        # Skills blocking interview conversion
        # Find applications sent that have no interviews
        stmt_apps = (
            select(JobApplication)
            .join(Job, JobApplication.job_id == Job.id)
            .join(ResumeVersion, JobApplication.resume_version_id == ResumeVersion.id)
            .where(
                JobApplication.user_id == user_id,
                Job.is_deleted == False,
                ResumeVersion.is_deleted == False
            )
        )
        res_apps = await self.db.execute(stmt_apps)
        apps = list(res_apps.scalars().all())

        blocking_counts = Counter()
        for app in apps:
            status = app.status.lower().strip()
            is_sent = status not in ("draft", "saved")
            is_int = (
                app.interview_at is not None or
                status in ("interview", "offer") or
                app.outcome_type in (OutcomeType.interviewed, OutcomeType.offered, OutcomeType.accepted)
            )
            # Blocking if sent but not interviewed
            if is_sent and not is_int:
                # Find skill gap analyses for this application's version and job
                # Match matches on resume_version_id and job_id
                app_gaps = [g for g in gaps if g.resume_version_id == app.resume_version_id]
                for g in app_gaps:
                    blocking_counts[g.missing_skill] += 1

        skills_blocking_interviews = [{"skill": k, "count": v} for k, v in blocking_counts.most_common(5)]

        return {
            "top_missing_skills": top_missing_skills,
            "most_frequent_gap_categories": most_frequent_gap_categories,
            "highest_impact_skills": highest_impact_skills,
            "skills_blocking_interviews": skills_blocking_interviews
        }
