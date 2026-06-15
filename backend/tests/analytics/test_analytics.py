"""Sprint 9 Integration Tests: Analytics Dashboard Foundation."""
import pytest
import pytest_asyncio
from uuid import UUID
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch
from httpx import AsyncClient
from sqlalchemy import select

from app.analytics.models import AnalyticsSnapshot, AnalyticsInsight
from app.applications.models import JobApplication, OutcomeType
from app.jobs.models import Job, JobMatch, SkillGapAnalysis
from app.resumes.models import ResumeVersion

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def mock_boto3():
    with patch("boto3.client") as mock_client:
        mock_s3 = MagicMock()
        mock_client.return_value = mock_s3
        yield mock_s3


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict:
    """Register and login a test user, return auth headers."""
    register_payload = {
        "email": "analyticsuser@example.com",
        "password": "strongpassword123",
        "full_name": "Analytics User",
    }
    await client.post("/api/v1/auth/register", json=register_payload)
    login_payload = {
        "email": "analyticsuser@example.com",
        "password": "strongpassword123",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    data = response.json()
    return {"Authorization": f"Bearer {data['access_token']}"}


@pytest_asyncio.fixture
async def second_auth_headers(client: AsyncClient) -> dict:
    """Register and login a second user, return auth headers."""
    register_payload = {
        "email": "analyticsuser2@example.com",
        "password": "strongpassword123",
        "full_name": "Analytics User 2",
    }
    await client.post("/api/v1/auth/register", json=register_payload)
    login_payload = {
        "email": "analyticsuser2@example.com",
        "password": "strongpassword123",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    data = response.json()
    return {"Authorization": f"Bearer {data['access_token']}"}


@pytest_asyncio.fixture
async def setup_analytics_data(client: AsyncClient, auth_headers: dict, db_session) -> tuple[str, str, str]:
    """Sets up resume version, jobs, matches, skill gaps, and applications for testing."""
    # 1. Create Job 1
    job_resp1 = await client.post("/api/v1/jobs", json={
        "title": "Cloud Engineer",
        "company": "Amazon AWS Inc",
        "description": "Proficient in AWS, Kubernetes, Python.",
        "location": "Seattle",
    }, headers=auth_headers)
    job_id1 = job_resp1.json()["id"]

    # 2. Create Resume Version
    from app.users.models import User
    user = (await db_session.execute(select(User).where(User.email == "analyticsuser@example.com"))).scalar_one()
    user_id = user.id

    # Create Resume Profile and Version directly in DB to bypass s3 uploads
    from app.resumes.models import ResumeProfile
    profile = ResumeProfile(user_id=user_id, name="Main Resume", is_default=True)
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(profile)

    version1 = ResumeVersion(
        profile_id=profile.id,
        user_id=user_id,
        version_number=1,
        original_filename="resume_v1.pdf",
        storage_path="path/to/resume_v1.pdf",
        file_size=12345,
        mime_type="application/pdf",
        upload_source="web",
        extracted_text="John Doe Cloud Specialist AWS Kubernetes Python",
        ats_score=85,
        skills=["aws", "kubernetes", "python"]
    )
    db_session.add(version1)
    await db_session.commit()
    await db_session.refresh(version1)

    version_id = str(version1.id)

    # 3. Create JobMatch
    match = JobMatch(
        user_id=user_id,
        resume_version_id=version1.id,
        job_id=UUID(job_id1),
        overall_match_score=90.0,
        skills_match_score=95.0,
        experience_match_score=85.0,
        education_match_score=90.0,
        keyword_match_score=90.0,
        missing_skills=["kubernetes"],
        matched_skills=["aws", "python"],
        fit_summary="Strong match."
    )
    db_session.add(match)
    await db_session.flush()

    # 4. Create SkillGapAnalysis
    gap = SkillGapAnalysis(
        user_id=user_id,
        resume_version_id=version1.id,
        job_match_id=match.id,
        missing_skill="kubernetes",
        importance_score=80,
        category="DevOps",
        learning_priority="high",
        estimated_learning_time="2 weeks",
        recommendation_reason="Highly requested in JD.",
        roadmap_priority_score=85
    )
    db_session.add(gap)
    await db_session.commit()

    # 5. Create Applications
    # App 1: applied -> interview -> offer
    app_resp = await client.post("/api/v1/applications", json={
        "job_id": job_id1,
        "resume_version_id": version_id,
        "status": "draft",
    }, headers=auth_headers)
    app_id = app_resp.json()["id"]

    await client.patch(f"/api/v1/applications/{app_id}/status", json={"status": "saved"}, headers=auth_headers)
    await client.patch(f"/api/v1/applications/{app_id}/status", json={"status": "applied"}, headers=auth_headers)
    await client.patch(f"/api/v1/applications/{app_id}/status", json={"status": "in_review"}, headers=auth_headers)
    await client.patch(f"/api/v1/applications/{app_id}/status", json={"status": "assessment"}, headers=auth_headers)
    await client.patch(f"/api/v1/applications/{app_id}/status", json={"status": "interview"}, headers=auth_headers)
    await client.patch(f"/api/v1/applications/{app_id}/status", json={"status": "offer"}, headers=auth_headers)

    return user_id, job_id1, version_id


# =============================================================================
# Integration Test Cases
# =============================================================================


async def test_analytics_generation_success(
    client: AsyncClient, auth_headers: dict, setup_analytics_data: tuple[str, str, str]
):
    """Test triggering snapshot generation and checking output response fields."""
    user_id, job_id, version_id = setup_analytics_data

    response = await client.post("/api/v1/analytics/generate", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert "snapshot" in data
    assert "resume_intelligence" in data
    assert "skill_intelligence" in data
    assert "insights" in data

    snap = data["snapshot"]
    assert snap["total_applications"] == 1
    assert snap["total_interviews"] == 1
    assert snap["total_offers"] == 1
    assert snap["interview_rate"] == 1.0
    assert snap["offer_rate"] == 1.0
    assert snap["acceptance_rate"] == 0.0
    assert snap["average_ats_score"] == 85.0
    assert snap["average_match_score"] == 0.90
    assert snap["ats_score_delta"] is None
    assert snap["match_score_delta"] is None

    # Funnel counts check
    funnel = snap["funnel_stage_counts"]
    assert funnel["offer"] == 1
    assert funnel["draft"] == 0

    # Strongest resume version
    assert snap["strongest_resume_version_id"] == version_id


async def test_snapshot_caching_and_idempotency(
    client: AsyncClient, auth_headers: dict, setup_analytics_data: tuple[str, str, str], db_session
):
    """Test that generation is cached within 1 hour and idempotent."""
    user_id, job_id, version_id = setup_analytics_data

    # Generate first snapshot
    resp1 = await client.post("/api/v1/analytics/generate", headers=auth_headers)
    snap1 = resp1.json()["snapshot"]

    # Generate second snapshot immediately - should be cached (same ID)
    resp2 = await client.post("/api/v1/analytics/generate", headers=auth_headers)
    snap2 = resp2.json()["snapshot"]
    assert snap1["id"] == snap2["id"]

    # Mock the first snapshot's generated_at to be >1 hour ago in DB
    stmt = select(AnalyticsSnapshot).where(AnalyticsSnapshot.id == UUID(snap1["id"]))
    db_snap = (await db_session.execute(stmt)).scalar_one()
    db_snap.generated_at = datetime.now(timezone.utc) - timedelta(hours=2)
    await db_session.commit()

    # Generate third snapshot - should create a NEW one with delta calculated
    resp3 = await client.post("/api/v1/analytics/generate", headers=auth_headers)
    snap3 = resp3.json()["snapshot"]
    assert snap1["id"] != snap3["id"]
    assert snap3["ats_score_delta"] == 0.0
    assert snap3["match_score_delta"] == 0.0
    assert snap3["interview_rate_delta"] == 0.0


async def test_analytics_ownership_protection(
    client: AsyncClient, auth_headers: dict, second_auth_headers: dict, setup_analytics_data: tuple[str, str, str]
):
    """Test that a second user does not see or trigger another user's analytics."""
    user_id, job_id, version_id = setup_analytics_data

    # User 1 generates analytics
    await client.post("/api/v1/analytics/generate", headers=auth_headers)

    # User 2 gets their own overview (should create a clean one with 0 applications)
    resp2 = await client.get("/api/v1/analytics", headers=second_auth_headers)
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["snapshot"]["total_applications"] == 0
    assert data2["snapshot"]["average_ats_score"] == 0.0


async def test_soft_delete_protection(
    client: AsyncClient, auth_headers: dict, setup_analytics_data: tuple[str, str, str]
):
    """Test that soft-deleted jobs or resumes are excluded from analytics metrics."""
    user_id, job_id, version_id = setup_analytics_data

    # Soft delete the job
    del_resp = await client.delete(f"/api/v1/jobs/{job_id}", headers=auth_headers)
    assert del_resp.status_code in (200, 204)

    # Generate analytics - application should be excluded because its job is soft-deleted
    resp = await client.post("/api/v1/analytics/generate", headers=auth_headers)
    snap = resp.json()["snapshot"]
    assert snap["total_applications"] == 0


async def test_history_retrieval(
    client: AsyncClient, auth_headers: dict, setup_analytics_data: tuple[str, str, str], db_session
):
    """Test retrieving history lists snapshots correctly."""
    user_id, job_id, version_id = setup_analytics_data

    # Generate snapshot 1
    resp1 = await client.post("/api/v1/analytics/generate", headers=auth_headers)
    snap1_id = resp1.json()["snapshot"]["id"]

    # Age it
    stmt = select(AnalyticsSnapshot).where(AnalyticsSnapshot.id == UUID(snap1_id))
    db_snap = (await db_session.execute(stmt)).scalar_one()
    db_snap.generated_at = datetime.now(timezone.utc) - timedelta(hours=2)
    await db_session.commit()

    # Generate snapshot 2
    resp2 = await client.post("/api/v1/analytics/generate", headers=auth_headers)
    snap2_id = resp2.json()["snapshot"]["id"]

    # Fetch history
    hist_resp = await client.get("/api/v1/analytics/history", headers=auth_headers)
    assert hist_resp.status_code == 200
    history = hist_resp.json()
    assert len(history) >= 2
    assert history[0]["id"] == snap2_id
    assert history[1]["id"] == snap1_id


async def test_insight_generation(
    client: AsyncClient, auth_headers: dict, setup_analytics_data: tuple[str, str, str]
):
    """Test that insights are created and persisted during snapshot generation."""
    user_id, job_id, version_id = setup_analytics_data

    # Generate snapshot & insights
    resp = await client.post("/api/v1/analytics/generate", headers=auth_headers)
    data = resp.json()
    insights = data["insights"]
    assert len(insights) > 0

    # Fetch insights separately
    ins_resp = await client.get("/api/v1/analytics/insights", headers=auth_headers)
    assert ins_resp.status_code == 200
    insights2 = ins_resp.json()
    assert len(insights2) == len(insights)
    assert insights2[0]["title"] is not None
