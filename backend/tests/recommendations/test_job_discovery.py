import pytest
import pytest_asyncio
import uuid
import hashlib
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.users.models import User
from app.resumes.models import ResumeProfile, ResumeVersion, ATSAnalysis
from app.jobs.models import Job, JobMatch, SkillGapAnalysis, SkillGap
from app.applications.models import JobApplication, OutcomeType
from app.roadmap.models import CareerRoadmap, RoadmapMilestone
from app.analytics.models import AnalyticsSnapshot
from app.recommendations.models import RecommendationSignal, JobRecommendation
from app.core.security import create_access_token

pytestmark = pytest.mark.asyncio


class DiscoveryTestData:
    def __init__(self):
        self.user_a_id = uuid.uuid4()
        self.user_b_id = uuid.uuid4()
        self.profile_a_id = uuid.uuid4()
        self.version_a_id = uuid.uuid4()
        self.job_1_id = uuid.uuid4()
        self.job_2_id = uuid.uuid4()
        self.job_b_id = uuid.uuid4()
        self.match_1_id = uuid.uuid4()
        self.match_2_id = uuid.uuid4()


@pytest_asyncio.fixture
async def setup_data(db_session: AsyncSession) -> DiscoveryTestData:
    setup = DiscoveryTestData()

    # 1. Create Users
    user_a = User(
        id=setup.user_a_id,
        email="usera@example.com",
        password_hash="hashed_pwd",
        full_name="User A",
        is_active=True,
    )
    user_b = User(
        id=setup.user_b_id,
        email="userb@example.com",
        password_hash="hashed_pwd",
        full_name="User B",
        is_active=True,
    )
    db_session.add_all([user_a, user_b])
    await db_session.flush()

    # 2. Create Resume Profile & Version
    profile_a = ResumeProfile(
        id=setup.profile_a_id,
        user_id=setup.user_a_id,
        name="Profile A",
        is_default=True,
    )
    db_session.add(profile_a)
    await db_session.flush()

    version_a = ResumeVersion(
        id=setup.version_a_id,
        profile_id=setup.profile_a_id,
        user_id=setup.user_a_id,
        version_number=1,
        original_filename="resume.pdf",
        storage_path="path/to/resume.pdf",
        file_size=1024,
        mime_type="application/pdf",
        upload_source="upload",
        skills=["Python", "FastAPI", "SQL"],
        status="completed",
    )
    db_session.add(version_a)
    await db_session.flush()

    profile_a.active_version_id = version_a.id
    await db_session.flush()

    # 3. Create Jobs
    job_1 = Job(
        id=setup.job_1_id,
        user_id=setup.user_a_id,
        title="Backend Engineer",
        company="TechCorp",
        description="Write Python FastAPI code and handle SQL database queries.",
        required_skills=["Python", "FastAPI", "SQL"],
    )
    job_2 = Job(
        id=setup.job_2_id,
        user_id=setup.user_a_id,
        title="Frontend Engineer",
        company="DesignCorp",
        description="Write frontend code using React, CSS, and HTML.",
        required_skills=["React", "CSS", "HTML"],
    )
    job_b = Job(
        id=setup.job_b_id,
        user_id=setup.user_b_id,
        title="Data Scientist",
        company="ResearchLab",
        description="Research data models.",
        required_skills=["Python", "Machine Learning"],
    )
    db_session.add_all([job_1, job_2, job_b])
    await db_session.flush()

    # 4. Create Job Matches
    match_1 = JobMatch(
        id=setup.match_1_id,
        user_id=setup.user_a_id,
        resume_version_id=setup.version_a_id,
        job_id=setup.job_1_id,
        overall_match_score=90.0,
        skills_match_score=95.0,
        experience_match_score=85.0,
        education_match_score=90.0,
        keyword_match_score=90.0,
        missing_skills=[],
        strengths=["FastAPI background"],
        weaknesses=[],
        fit_summary="Excellent fit",
        improvement_actions=[],
    )
    match_2 = JobMatch(
        id=setup.match_2_id,
        user_id=setup.user_a_id,
        resume_version_id=setup.version_a_id,
        job_id=setup.job_2_id,
        overall_match_score=30.0,
        skills_match_score=20.0,
        experience_match_score=40.0,
        education_match_score=40.0,
        keyword_match_score=30.0,
        missing_skills=["React", "CSS", "HTML"],
        strengths=[],
        weaknesses=["Missing frontend stack"],
        fit_summary="Weak fit",
        improvement_actions=[],
    )
    db_session.add_all([match_1, match_2])
    await db_session.flush()

    # 5. Create ATS Analysis
    jd_1_hash = hashlib.sha256(job_1.description.strip().encode("utf-8")).hexdigest()
    ats_1 = ATSAnalysis(
        resume_version_id=setup.version_a_id,
        job_description_hash=jd_1_hash,
        ats_score=85,
        keyword_score=80,
        skills_score=90,
        experience_score=85,
        education_score=90,
    )
    db_session.add(ats_1)
    await db_session.flush()

    # 6. Create Analytics Snapshot
    snapshot = AnalyticsSnapshot(
        user_id=setup.user_a_id,
        total_applications=0,
        total_interviews=0,
        total_offers=0,
        total_rejections=0,
        total_acceptances=0,
        response_rate=0.0,
        interview_rate=0.0,
        offer_rate=0.0,
        acceptance_rate=0.0,
        average_ats_score=0.0,
        average_match_score=0.0,
        strongest_resume_version_id=setup.version_a_id,
    )
    db_session.add(snapshot)
    await db_session.flush()

    await db_session.commit()
    return setup


async def get_headers_for_user(user_id: uuid.UUID) -> dict:
    token = create_access_token(subject=user_id)
    return {"Authorization": f"Bearer {token}"}


async def test_recommendation_generation_success(
    client: AsyncClient, db_session: AsyncSession, setup_data: DiscoveryTestData
):
    headers = await get_headers_for_user(setup_data.user_a_id)

    response = await client.post("/api/v1/recommendations/generate", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert "recommendations" in data
    assert data["total_recommendations"] == 3
    assert "generated_at" in data

    recs = data["recommendations"]
    assert recs[0]["job_id"] == str(setup_data.job_1_id)
    assert recs[0]["recommendation_score"] > recs[1]["recommendation_score"]
    assert "recommendation_reason" in recs[0]
    assert recs[0]["confidence_score"] == 100.0  # JobMatch + ATSAnalysis = 100%
    assert recs[0]["recommendation_status"] == "recommended"
    assert recs[0]["job_snapshot"]["title"] == "Backend Engineer"
    assert recs[0]["job_snapshot"]["company"] == "TechCorp"


async def test_recommendation_cache_reuse(
    client: AsyncClient, db_session: AsyncSession, setup_data: DiscoveryTestData
):
    headers = await get_headers_for_user(setup_data.user_a_id)

    # 1. First call generates recommendations
    resp1 = await client.get("/api/v1/recommendations", headers=headers)
    assert resp1.status_code == 200
    data1 = resp1.json()

    # 2. Modify job_match overall score in DB
    stmt = select(JobMatch).where(JobMatch.id == setup_data.match_1_id)
    match_1 = (await db_session.execute(stmt)).scalar_one()
    match_1.overall_match_score = 10.0
    await db_session.commit()

    # 3. Second call should return cached recommendation (with original high score)
    resp2 = await client.get("/api/v1/recommendations", headers=headers)
    assert resp2.status_code == 200
    data2 = resp2.json()

    assert data1["recommendations"][0]["recommendation_score"] == data2["recommendations"][0]["recommendation_score"]


async def test_recommendation_refresh(
    client: AsyncClient, db_session: AsyncSession, setup_data: DiscoveryTestData
):
    headers = await get_headers_for_user(setup_data.user_a_id)

    # 1. Generate cache
    resp1 = await client.get("/api/v1/recommendations", headers=headers)
    assert resp1.status_code == 200
    score_before = resp1.json()["recommendations"][0]["recommendation_score"]

    # 2. Modify job_match overall score in DB
    stmt = select(JobMatch).where(JobMatch.id == setup_data.match_1_id)
    match_1 = (await db_session.execute(stmt)).scalar_one()
    match_1.overall_match_score = 10.0
    await db_session.commit()

    # 3. Refresh recommendations (cache bypass)
    resp2 = await client.post("/api/v1/recommendations/refresh", headers=headers)
    assert resp2.status_code == 200
    score_after = resp2.json()["recommendations"][0]["recommendation_score"]

    # The scores should change because the cache was purged and recalculated
    assert score_before != score_after


async def test_ownership_protection(
    client: AsyncClient, db_session: AsyncSession, setup_data: DiscoveryTestData
):
    # User B has no jobs or resume versions
    headers_b = await get_headers_for_user(setup_data.user_b_id)

    # Call get recommendations for User B - should fail or return 0 recommendations
    response = await client.post("/api/v1/recommendations/generate", headers=headers_b)
    # Since User B has no resume version, it should return 404
    assert response.status_code == 404
    assert response.json()["detail"] == "No active resume version found for user"


async def test_soft_delete_protection(
    client: AsyncClient, db_session: AsyncSession, setup_data: DiscoveryTestData
):
    headers = await get_headers_for_user(setup_data.user_a_id)

    # Soft-delete Job 1
    stmt = select(Job).where(Job.id == setup_data.job_1_id)
    job_1 = (await db_session.execute(stmt)).scalar_one()
    job_1.is_deleted = True
    await db_session.commit()

    response = await client.post("/api/v1/recommendations/generate", headers=headers)
    assert response.status_code == 200
    data = response.json()
    # Should only contain 2 recommendations (Job 2 and Job B) since Job 1 is soft-deleted
    assert data["total_recommendations"] == 2
    # Ensure Job 1 is not returned
    rec_job_ids = [r["job_id"] for r in data["recommendations"]]
    assert str(setup_data.job_1_id) not in rec_job_ids


async def test_scoring_determinism(
    client: AsyncClient, db_session: AsyncSession, setup_data: DiscoveryTestData
):
    headers = await get_headers_for_user(setup_data.user_a_id)

    # Double generate and assert identical scores
    resp1 = await client.post("/api/v1/recommendations/generate", headers=headers)
    resp2 = await client.post("/api/v1/recommendations/generate", headers=headers)

    recs1 = resp1.json()["recommendations"]
    recs2 = resp2.json()["recommendations"]

    assert len(recs1) == len(recs2)
    for r1, r2 in zip(recs1, recs2):
        assert r1["job_id"] == r2["job_id"]
        assert r1["recommendation_score"] == r2["recommendation_score"]


async def test_recommendation_reason_generation(
    client: AsyncClient, db_session: AsyncSession, setup_data: DiscoveryTestData
):
    headers = await get_headers_for_user(setup_data.user_a_id)

    response = await client.post("/api/v1/recommendations/generate", headers=headers)
    assert response.status_code == 200
    recs = response.json()["recommendations"]

    # Job 1 has 90% match score and 85% ATS score
    rec_1 = recs[0]
    assert rec_1["recommendation_reason"]["high_match_score"] is True
    assert rec_1["recommendation_reason"]["ats_compatible"] is True

    # Job 2 has low scores
    rec_2 = recs[1]
    assert rec_2["recommendation_reason"]["high_match_score"] is False
    assert rec_2["recommendation_reason"]["ats_compatible"] is False


async def test_recommendation_ordering(
    client: AsyncClient, db_session: AsyncSession, setup_data: DiscoveryTestData
):
    headers = await get_headers_for_user(setup_data.user_a_id)

    response = await client.post("/api/v1/recommendations/generate", headers=headers)
    assert response.status_code == 200
    recs = response.json()["recommendations"]

    # Ordering check (descending recommendation_score)
    scores = [r["recommendation_score"] for r in recs]
    assert scores == sorted(scores, reverse=True)


async def test_feedback_signal_influence(
    client: AsyncClient, db_session: AsyncSession, setup_data: DiscoveryTestData
):
    headers = await get_headers_for_user(setup_data.user_a_id)

    # 1. Generate baseline
    resp1 = await client.post("/api/v1/recommendations/generate", headers=headers)
    score_before = resp1.json()["recommendations"][0]["recommendation_score"]

    # 2. Emit a negative feedback signal for Job 1
    # Create a recommendation signal rejection_received for User A
    sig = RecommendationSignal(
        user_id=setup_data.user_a_id,
        job_match_id=setup_data.match_1_id,
        signal_type="rejection_received",
        signal_source="application",
        signal_value=-1.0,
        confidence_score=1.0,
        signal_weight=1.0,
    )
    db_session.add(sig)
    await db_session.commit()

    # 3. Regenerate and check score decreased
    resp2 = await client.post("/api/v1/recommendations/generate", headers=headers)
    score_after = resp2.json()["recommendations"][0]["recommendation_score"]

    assert score_after < score_before


async def test_roadmap_progress_influence(
    client: AsyncClient, db_session: AsyncSession, setup_data: DiscoveryTestData
):
    headers = await get_headers_for_user(setup_data.user_a_id)

    # Modify match_1 in DB to have a missing skill so there is a skill gap penalty
    stmt = select(JobMatch).where(JobMatch.id == setup_data.match_1_id)
    match_1 = (await db_session.execute(stmt)).scalar_one()
    match_1.missing_skills = ["SQL"]
    await db_session.commit()

    # 1. Generate baseline
    resp1 = await client.post("/api/v1/recommendations/generate", headers=headers)
    recs1 = resp1.json()["recommendations"]
    assert recs1[0]["recommendation_reason"]["roadmap_progress_helpful"] is False


    # 2. Add CareerRoadmap with completed milestones for Job 1
    roadmap = CareerRoadmap(
        id=uuid.uuid4(),
        user_id=setup_data.user_a_id,
        resume_version_id=setup_data.version_a_id,
        job_match_id=setup_data.match_1_id,
        total_estimated_weeks=4,
    )
    db_session.add(roadmap)
    await db_session.flush()

    milestone = RoadmapMilestone(
        id=uuid.uuid4(),
        roadmap_id=roadmap.id,
        skill_gap_id=uuid.uuid4(),  # Mock skill gap id
        milestone_order=1,
        milestone_title="Learn advanced SQL queries",
        estimated_weeks=2,
        priority_score=10,
        completion_status="completed",  # Done!
    )
    db_session.add(milestone)
    await db_session.commit()

    # 3. Regenerate recommendations
    resp2 = await client.post("/api/v1/recommendations/generate", headers=headers)
    recs2 = resp2.json()["recommendations"]

    assert recs2[0]["recommendation_reason"]["roadmap_progress_helpful"] is True
    # Score should increase because skill_gap_score gets roadmap progress bonus
    assert recs2[0]["recommendation_score"] > recs1[0]["recommendation_score"]


async def test_recommendation_status_tracking(
    client: AsyncClient, db_session: AsyncSession, setup_data: DiscoveryTestData
):
    headers = await get_headers_for_user(setup_data.user_a_id)

    # 1. Generate recommendations
    resp = await client.post("/api/v1/recommendations/generate", headers=headers)
    assert resp.status_code == 200
    recs = resp.json()["recommendations"]
    rec_1 = recs[0]
    rec_id = rec_1["id"]

    # Default status should be "recommended"
    assert rec_1["recommendation_status"] == "recommended"

    # 2. Update status to "viewed" via API
    patch_resp = await client.patch(
        f"/api/v1/recommendations/{rec_id}/status",
        json={"status": "viewed"},
        headers=headers
    )
    assert patch_resp.status_code == 200
    data = patch_resp.json()
    assert data["recommendation_status"] == "viewed"

    # 3. Retrieve recommendations and verify the updated status persists in cache
    get_resp = await client.get("/api/v1/recommendations", headers=headers)
    assert get_resp.status_code == 200
    get_recs = get_resp.json()["recommendations"]
    # Job 1's recommendation (by ID) should have status "viewed"
    matching_rec = [r for r in get_recs if r["id"] == rec_id][0]
    assert matching_rec["recommendation_status"] == "viewed"

    # 4. Access control protection: User B tries to update User A's recommendation
    headers_b = await get_headers_for_user(setup_data.user_b_id)
    patch_resp_b = await client.patch(
        f"/api/v1/recommendations/{rec_id}/status",
        json={"status": "saved"},
        headers=headers_b
    )
    # Ownership violation must return 404
    assert patch_resp_b.status_code == 404


async def test_job_snapshot_preservation(
    client: AsyncClient, db_session: AsyncSession, setup_data: DiscoveryTestData
):
    headers = await get_headers_for_user(setup_data.user_a_id)

    # 1. Generate recommendations
    resp = await client.post("/api/v1/recommendations/generate", headers=headers)
    assert resp.status_code == 200
    recs = resp.json()["recommendations"]
    rec_1 = recs[0]
    rec_id = rec_1["id"]
    job_id = rec_1["job_id"]
    original_title = rec_1["job_snapshot"]["title"]

    # 2. Modify original Job in database
    stmt = select(Job).where(Job.id == uuid.UUID(job_id))
    job_record = (await db_session.execute(stmt)).scalar_one()
    job_record.title = "Completely Different Title"
    await db_session.commit()

    # 3. Fetch recommendations
    get_resp = await client.get("/api/v1/recommendations", headers=headers)
    assert get_resp.status_code == 200
    get_recs = get_resp.json()["recommendations"]
    matching_rec = [r for r in get_recs if r["id"] == rec_id][0]

    # 4. Verify snapshot remains unchanged
    assert matching_rec["job_snapshot"]["title"] == original_title


async def test_saved_recommendations_endpoint(
    client: AsyncClient, db_session: AsyncSession, setup_data: DiscoveryTestData
):
    headers = await get_headers_for_user(setup_data.user_a_id)

    # 1. Generate recommendations
    resp = await client.post("/api/v1/recommendations/generate", headers=headers)
    assert resp.status_code == 200
    recs = resp.json()["recommendations"]
    rec_id = recs[0]["id"]

    # 2. Fetch saved - should be empty initially
    saved_resp = await client.get("/api/v1/recommendations/saved", headers=headers)
    assert saved_resp.status_code == 200
    assert saved_resp.json()["total_recommendations"] == 0

    # 3. Update status to "saved"
    patch_resp = await client.patch(
        f"/api/v1/recommendations/{rec_id}/status",
        json={"status": "saved"},
        headers=headers
    )
    assert patch_resp.status_code == 200

    # 4. Fetch saved - should return the saved recommendation
    saved_resp_2 = await client.get("/api/v1/recommendations/saved", headers=headers)
    assert saved_resp_2.status_code == 200
    data = saved_resp_2.json()
    assert data["total_recommendations"] == 1
    assert data["recommendations"][0]["id"] == rec_id


