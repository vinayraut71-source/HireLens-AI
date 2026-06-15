"""Sprint 10 Integration Tests: Feedback Learning Loop Foundation."""
import pytest
import pytest_asyncio
from uuid import UUID
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch
from httpx import AsyncClient
from sqlalchemy import select

from app.recommendations.models import RecommendationSignal
from app.applications.models import JobApplication, OutcomeType
from app.jobs.models import Job, JobMatch, SkillGapAnalysis
from app.resumes.models import ResumeVersion
from app.roadmap.models import CareerRoadmap, RoadmapMilestone

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
        "email": "feedbackuser@example.com",
        "password": "strongpassword123",
        "full_name": "Feedback User",
    }
    await client.post("/api/v1/auth/register", json=register_payload)
    login_payload = {
        "email": "feedbackuser@example.com",
        "password": "strongpassword123",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    data = response.json()
    return {"Authorization": f"Bearer {data['access_token']}"}


@pytest_asyncio.fixture
async def second_auth_headers(client: AsyncClient) -> dict:
    """Register and login a second user, return auth headers."""
    register_payload = {
        "email": "feedbackuser2@example.com",
        "password": "strongpassword123",
        "full_name": "Feedback User 2",
    }
    await client.post("/api/v1/auth/register", json=register_payload)
    login_payload = {
        "email": "feedbackuser2@example.com",
        "password": "strongpassword123",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    data = response.json()
    return {"Authorization": f"Bearer {data['access_token']}"}


@pytest_asyncio.fixture
async def setup_feedback_data(client: AsyncClient, auth_headers: dict, db_session) -> tuple[str, str, str, str]:
    """Sets up resume version, jobs, matches, milestones, and applications for testing."""
    # 1. Create Job
    job_resp = await client.post("/api/v1/jobs", json={
        "title": "React Developer",
        "company": "UI Corp",
        "description": "Proficient in React, TypeScript, Redux.",
        "location": "Remote",
    }, headers=auth_headers)
    job_id = job_resp.json()["id"]

    # 2. Create Resume Version
    from app.users.models import User
    user = (await db_session.execute(select(User).where(User.email == "feedbackuser@example.com"))).scalar_one()
    user_id = user.id

    from app.resumes.models import ResumeProfile
    profile = ResumeProfile(user_id=user_id, name="Feedback Profile", is_default=True)
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
        extracted_text="John Doe Frontend React TypeScript Redux",
        ats_score=82,
        skills=["react", "typescript", "redux"]
    )
    db_session.add(version1)
    await db_session.commit()
    await db_session.refresh(version1)

    version_id = str(version1.id)

    # 3. Create JobMatch
    match = JobMatch(
        user_id=user_id,
        resume_version_id=version1.id,
        job_id=UUID(job_id),
        overall_match_score=85.0,
        skills_match_score=90.0,
        experience_match_score=80.0,
        education_match_score=85.0,
        keyword_match_score=85.0,
        missing_skills=[],
        matched_skills=["react", "typescript"],
        fit_summary="React fit."
    )
    db_session.add(match)
    await db_session.flush()

    # 4. Create SkillGapAnalysis
    gap = SkillGapAnalysis(
        user_id=user_id,
        resume_version_id=version1.id,
        job_match_id=match.id,
        missing_skill="redux",
        importance_score=80,
        category="Frontend",
        learning_priority="high",
        estimated_learning_time="2 weeks",
        recommendation_reason="Highly requested in JD.",
        roadmap_priority_score=85
    )
    db_session.add(gap)
    await db_session.flush()

    # 5. Create Roadmap & Milestone
    roadmap = CareerRoadmap(
        user_id=user_id,
        resume_version_id=version1.id,
        job_match_id=match.id,
        total_estimated_weeks=4,
        roadmap_status="active"
    )
    db_session.add(roadmap)
    await db_session.flush()

    milestone = RoadmapMilestone(
        roadmap_id=roadmap.id,
        skill_gap_id=gap.id,
        milestone_order=1,
        milestone_title="Learn Redux Toolkit",
        estimated_weeks=2,
        priority_score=90,
        completion_status="completed"
    )
    db_session.add(milestone)
    await db_session.commit()

    # 5. Create Application and move to interview
    app_resp = await client.post("/api/v1/applications", json={
        "job_id": job_id,
        "resume_version_id": version_id,
        "status": "draft",
    }, headers=auth_headers)
    app_id = app_resp.json()["id"]

    await client.patch(f"/api/v1/applications/{app_id}/status", json={"status": "saved"}, headers=auth_headers)
    await client.patch(f"/api/v1/applications/{app_id}/status", json={"status": "applied"}, headers=auth_headers)
    await client.patch(f"/api/v1/applications/{app_id}/status", json={"status": "in_review"}, headers=auth_headers)
    await client.patch(f"/api/v1/applications/{app_id}/status", json={"status": "assessment"}, headers=auth_headers)
    await client.patch(f"/api/v1/applications/{app_id}/status", json={"status": "interview"}, headers=auth_headers)

    return user_id, job_id, version_id, app_id


# =============================================================================
# Integration Test Cases
# =============================================================================


async def test_feedback_generation_success(
    client: AsyncClient, auth_headers: dict, setup_feedback_data: tuple[str, str, str, str]
):
    """Test generating recommendation signals from application outcomes & milestones."""
    user_id, job_id, version_id, app_id = setup_feedback_data

    response = await client.post("/api/v1/feedback/generate", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert data["generated_count"] >= 2  # interview_received, high_match_success, roadmap_completed
    assert data["skipped_count"] == 0

    # Fetch signals
    sig_resp = await client.get("/api/v1/feedback/signals", headers=auth_headers)
    assert sig_resp.status_code == 200
    signals = sig_resp.json()

    sig_types = [s["signal_type"] for s in signals]
    assert "interview_received" in sig_types
    assert "high_match_success" in sig_types
    assert "roadmap_completed" in sig_types

    # Verify attributes
    int_sig = next(s for s in signals if s["signal_type"] == "interview_received")
    assert int_sig["application_id"] == app_id
    assert int_sig["signal_value"] == 1.0
    assert int_sig["confidence_score"] == 0.90
    assert int_sig["signal_source"] == "application"
    assert int_sig["signal_weight"] == 0.90

    hm_sig = next(s for s in signals if s["signal_type"] == "high_match_success")
    assert hm_sig["signal_source"] == "job_match"
    assert hm_sig["signal_weight"] == 1.275

    rm_sig = next(s for s in signals if s["signal_type"] == "roadmap_completed")
    assert rm_sig["signal_source"] == "roadmap"
    assert rm_sig["signal_weight"] == 0.45


async def test_duplicate_prevention(
    client: AsyncClient, auth_headers: dict, setup_feedback_data: tuple[str, str, str, str]
):
    """Test that regenerating signals is idempotent and skips duplicates."""
    user_id, job_id, version_id, app_id = setup_feedback_data

    # Generate first time
    resp1 = await client.post("/api/v1/feedback/generate", headers=auth_headers)
    gen_count1 = resp1.json()["generated_count"]
    assert gen_count1 >= 2

    # Generate second time - should skip all duplicates
    resp2 = await client.post("/api/v1/feedback/generate", headers=auth_headers)
    data2 = resp2.json()
    assert data2["generated_count"] == 0
    assert data2["skipped_count"] == gen_count1


async def test_ownership_protection(
    client: AsyncClient, auth_headers: dict, second_auth_headers: dict, setup_feedback_data: tuple[str, str, str, str]
):
    """Test user boundary separation - second user cannot see first user's signals."""
    user_id, job_id, version_id, app_id = setup_feedback_data

    # User 1 generates signals
    await client.post("/api/v1/feedback/generate", headers=auth_headers)

    # User 2 gets signals list (should be empty)
    resp2 = await client.get("/api/v1/feedback/signals", headers=second_auth_headers)
    assert resp2.status_code == 200
    assert len(resp2.json()) == 0


async def test_soft_delete_protection(
    client: AsyncClient, auth_headers: dict, setup_feedback_data: tuple[str, str, str, str]
):
    """Test that application outcome signals are ignored when job is soft-deleted."""
    user_id, job_id, version_id, app_id = setup_feedback_data

    # Soft delete the job
    del_resp = await client.delete(f"/api/v1/jobs/{job_id}", headers=auth_headers)
    assert del_resp.status_code in (200, 204)

    # Generate signals - should only generate roadmap_completed (application/match ignored)
    resp = await client.post("/api/v1/feedback/generate", headers=auth_headers)
    data = resp.json()

    # Fetch signals list
    sig_resp = await client.get("/api/v1/feedback/signals", headers=auth_headers)
    signals = sig_resp.json()
    sig_types = [s["signal_type"] for s in signals]
    assert "roadmap_completed" in sig_types
    assert "interview_received" not in sig_types


async def test_summary_generation(
    client: AsyncClient, auth_headers: dict, setup_feedback_data: tuple[str, str, str, str]
):
    """Test generating aggregated feedback summary."""
    user_id, job_id, version_id, app_id = setup_feedback_data

    # Generate signals first
    await client.post("/api/v1/feedback/generate", headers=auth_headers)

    # Get summary
    sum_resp = await client.get("/api/v1/feedback/summary", headers=auth_headers)
    assert sum_resp.status_code == 200
    summary = sum_resp.json()

    assert "skills_success" in summary
    assert "best_performing_resumes" in summary
    assert "highest_converting_categories" in summary

    # Verify skill success lists normalized skills (e.g. react, typescript)
    success_skills = [s["skill"] for s in summary["skills_success"]]
    assert "react" in success_skills

    # Resume performance metrics check
    best_res = summary["best_performing_resumes"]
    assert len(best_res) == 1
    assert best_res[0]["id"] == version_id
    assert best_res[0]["interview_rate"] == 1.0
