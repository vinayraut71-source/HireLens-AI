"""Sprint 8 Integration Tests: Application Tracking Engine."""
import pytest
import pytest_asyncio
from uuid import UUID
from unittest.mock import MagicMock, patch
from httpx import AsyncClient
from sqlalchemy import select

from app.applications.models import JobApplication, ApplicationTimelineEvent
from app.jobs.models import Job
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
        "email": "appuser@example.com",
        "password": "strongpassword123",
        "full_name": "App User",
    }
    await client.post("/api/v1/auth/register", json=register_payload)
    login_payload = {
        "email": "appuser@example.com",
        "password": "strongpassword123",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    data = response.json()
    return {"Authorization": f"Bearer {data['access_token']}"}


@pytest_asyncio.fixture
async def second_auth_headers(client: AsyncClient) -> dict:
    """Register and login a second user for ownership tests."""
    register_payload = {
        "email": "appuser2@example.com",
        "password": "strongpassword123",
        "full_name": "App User 2",
    }
    await client.post("/api/v1/auth/register", json=register_payload)
    login_payload = {
        "email": "appuser2@example.com",
        "password": "strongpassword123",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    data = response.json()
    return {"Authorization": f"Bearer {data['access_token']}"}


@pytest_asyncio.fixture
async def setup_job_and_resume(client: AsyncClient, auth_headers: dict, mock_boto3) -> tuple[str, str]:
    """Create a job and a parsed resume version, returning their IDs."""
    resume_text = "John Doe\npython django docker postgres developer"
    mock_boto3.get_object.return_value = {
        "Body": MagicMock(read=lambda: resume_text.encode("utf-8"))
    }

    files = {"file": ("resume.pdf", b"mock content", "application/pdf")}
    upload_resp = await client.post("/api/v1/resumes/upload", files=files, headers=auth_headers)
    version_id = upload_resp.json()["id"]

    # Parse
    with patch("app.resumes.service.pdfplumber") as mock_pdf:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = resume_text
        mock_pdf_obj = MagicMock()
        mock_pdf_obj.pages = [mock_page]
        mock_pdf_obj.__enter__ = MagicMock(return_value=mock_pdf_obj)
        mock_pdf_obj.__exit__ = MagicMock(return_value=False)
        mock_pdf.open.return_value = mock_pdf_obj

        await client.post(f"/api/v1/resumes/{version_id}/parse", headers=auth_headers)

    # Job
    job_resp = await client.post("/api/v1/jobs", json={
        "title": "Python Developer",
        "description": "proficient in Python and Django and Docker.",
        "company": "TechInc",
    }, headers=auth_headers)
    job_id = job_resp.json()["id"]

    return job_id, version_id


# =============================================================================
# Application Tracking Engine Tests
# =============================================================================


async def test_create_application_success(
    client: AsyncClient, auth_headers: dict, setup_job_and_resume: tuple[str, str]
):
    """Test creating/tracking a new job application."""
    job_id, resume_version_id = setup_job_and_resume

    payload = {
        "job_id": job_id,
        "resume_version_id": resume_version_id,
        "status": "draft",
        "source": "LinkedIn",
        "notes": "First dynamic application",
    }
    response = await client.post("/api/v1/applications", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()

    assert "id" in data
    assert data["job_id"] == job_id
    assert data["resume_version_id"] == resume_version_id
    assert data["status"] == "draft"
    assert data["outcome_type"] == "unknown"
    assert data["job_snapshot"]["title"] == "Python Developer"
    assert data["job_snapshot"]["company"] == "TechInc"
    assert data["job_snapshot"]["location"] is None
    assert data["job_snapshot"]["salary"] is None
    assert data["job_snapshot"]["url"] is None
    assert data["source"] == "LinkedIn"
    assert data["notes"] == "First dynamic application"
    assert "created_at" in data
    assert "updated_at" in data


async def test_create_application_initial_timeline_event(
    client: AsyncClient, auth_headers: dict, setup_job_and_resume: tuple[str, str]
):
    """Test that creating an application creates an initial timeline event."""
    job_id, resume_version_id = setup_job_and_resume
    payload = {
        "job_id": job_id,
        "resume_version_id": resume_version_id,
        "status": "draft",
    }
    create_resp = await client.post("/api/v1/applications", json=payload, headers=auth_headers)
    app_id = create_resp.json()["id"]

    # Fetch timeline
    timeline_resp = await client.get(f"/api/v1/applications/{app_id}/timeline", headers=auth_headers)
    assert timeline_resp.status_code == 200
    timeline = timeline_resp.json()
    assert len(timeline) == 1
    assert timeline[0]["event_type"] == "created"
    assert timeline[0]["previous_status"] is None
    assert timeline[0]["new_status"] == "draft"


async def test_status_progression_valid(
    client: AsyncClient, auth_headers: dict, setup_job_and_resume: tuple[str, str]
):
    """Test advancing the application status along the valid path."""
    job_id, resume_version_id = setup_job_and_resume
    create_resp = await client.post("/api/v1/applications", json={
        "job_id": job_id,
        "resume_version_id": resume_version_id,
        "status": "draft",
    }, headers=auth_headers)
    app_id = create_resp.json()["id"]

    # Flow: draft -> saved -> applied -> in_review -> assessment -> interview -> offer
    path = ["saved", "applied", "in_review", "assessment", "interview", "offer"]
    for status in path:
        patch_resp = await client.patch(
            f"/api/v1/applications/{app_id}/status",
            json={"status": status, "notes": f"Moved to {status}"},
            headers=auth_headers,
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["status"] == status

    # Verify timeline length: 1 (created) + 6 (status transitions) = 7
    timeline_resp = await client.get(f"/api/v1/applications/{app_id}/timeline", headers=auth_headers)
    assert len(timeline_resp.json()) == 7


async def test_status_progression_alternative_exit_rejection(
    client: AsyncClient, auth_headers: dict, setup_job_and_resume: tuple[str, str]
):
    """Test transition from interview -> rejected."""
    job_id, resume_version_id = setup_job_and_resume
    create_resp = await client.post("/api/v1/applications", json={
        "job_id": job_id,
        "resume_version_id": resume_version_id,
        "status": "draft",
    }, headers=auth_headers)
    app_id = create_resp.json()["id"]

    # draft -> saved -> applied -> in_review -> assessment -> interview -> rejected
    path = ["saved", "applied", "in_review", "assessment", "interview", "rejected"]
    for status in path:
        patch_resp = await client.patch(
            f"/api/v1/applications/{app_id}/status", json={"status": status}, headers=auth_headers
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["status"] == status


async def test_status_progression_any_to_withdrawn(
    client: AsyncClient, auth_headers: dict, setup_job_and_resume: tuple[str, str]
):
    """Test transition from applied -> withdrawn."""
    job_id, resume_version_id = setup_job_and_resume
    create_resp = await client.post("/api/v1/applications", json={
        "job_id": job_id,
        "resume_version_id": resume_version_id,
        "status": "draft",
    }, headers=auth_headers)
    app_id = create_resp.json()["id"]

    # draft -> saved -> applied -> withdrawn
    path = ["saved", "applied", "withdrawn"]
    for status in path:
        patch_resp = await client.patch(
            f"/api/v1/applications/{app_id}/status", json={"status": status}, headers=auth_headers
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["status"] == status


async def test_status_progression_invalid(
    client: AsyncClient, auth_headers: dict, setup_job_and_resume: tuple[str, str]
):
    """Test that invalid status transitions are rejected with HTTP 400."""
    job_id, resume_version_id = setup_job_and_resume
    create_resp = await client.post("/api/v1/applications", json={
        "job_id": job_id,
        "resume_version_id": resume_version_id,
        "status": "draft",
    }, headers=auth_headers)
    app_id = create_resp.json()["id"]

    # draft -> interview directly (invalid)
    patch_resp = await client.patch(
        f"/api/v1/applications/{app_id}/status", json={"status": "interview"}, headers=auth_headers
    )
    assert patch_resp.status_code == 400


async def test_idempotent_status_updates(
    client: AsyncClient, auth_headers: dict, setup_job_and_resume: tuple[str, str]
):
    """Test that submitting the same status twice is idempotent (returns 200 but doesn't add timeline event)."""
    job_id, resume_version_id = setup_job_and_resume
    create_resp = await client.post("/api/v1/applications", json={
        "job_id": job_id,
        "resume_version_id": resume_version_id,
        "status": "draft",
    }, headers=auth_headers)
    app_id = create_resp.json()["id"]

    # Update to draft again
    patch_resp = await client.patch(
        f"/api/v1/applications/{app_id}/status", json={"status": "draft"}, headers=auth_headers
    )
    assert patch_resp.status_code == 200

    # Timeline should still only have 1 event
    timeline_resp = await client.get(f"/api/v1/applications/{app_id}/timeline", headers=auth_headers)
    assert len(timeline_resp.json()) == 1


async def test_application_ownership_protection(
    client: AsyncClient, auth_headers: dict, second_auth_headers: dict, setup_job_and_resume: tuple[str, str]
):
    """Test that a second user cannot view or update another user's application."""
    job_id, resume_version_id = setup_job_and_resume
    create_resp = await client.post("/api/v1/applications", json={
        "job_id": job_id,
        "resume_version_id": resume_version_id,
        "status": "draft",
    }, headers=auth_headers)
    app_id = create_resp.json()["id"]

    # User 2 tries to GET
    get_resp = await client.get(f"/api/v1/applications/{app_id}", headers=second_auth_headers)
    assert get_resp.status_code == 404

    # User 2 tries to PATCH
    patch_resp = await client.patch(
        f"/api/v1/applications/{app_id}/status", json={"status": "saved"}, headers=second_auth_headers
    )
    assert patch_resp.status_code == 404

    # User 2 tries to GET timeline
    time_resp = await client.get(f"/api/v1/applications/{app_id}/timeline", headers=second_auth_headers)
    assert time_resp.status_code == 404


async def test_soft_delete_protection_creation(
    client: AsyncClient, auth_headers: dict, setup_job_and_resume: tuple[str, str]
):
    """Test soft-delete protection prevents creating applications for deleted jobs or resumes."""
    job_id, resume_version_id = setup_job_and_resume

    # Soft-delete the job
    await client.delete(f"/api/v1/jobs/{job_id}", headers=auth_headers)

    # Creating application should fail with 404
    payload = {
        "job_id": job_id,
        "resume_version_id": resume_version_id,
        "status": "draft",
    }
    response = await client.post("/api/v1/applications", json=payload, headers=auth_headers)
    assert response.status_code == 404


async def test_soft_delete_protection_fetching(
    client: AsyncClient, auth_headers: dict, setup_job_and_resume: tuple[str, str]
):
    """Test that fetching or listing applications excludes those with soft-deleted jobs/resumes."""
    job_id, resume_version_id = setup_job_and_resume

    # Create application first
    create_resp = await client.post("/api/v1/applications", json={
        "job_id": job_id,
        "resume_version_id": resume_version_id,
        "status": "draft",
    }, headers=auth_headers)
    app_id = create_resp.json()["id"]

    # Verify list shows 1 item
    list_resp = await client.get("/api/v1/applications", headers=auth_headers)
    assert len(list_resp.json()) == 1

    # Soft-delete the job
    await client.delete(f"/api/v1/jobs/{job_id}", headers=auth_headers)

    # Fetch app directly -> 404
    get_resp = await client.get(f"/api/v1/applications/{app_id}", headers=auth_headers)
    assert get_resp.status_code == 404

    # Verify list shows 0 items
    list_resp2 = await client.get("/api/v1/applications", headers=auth_headers)
    assert len(list_resp2.json()) == 0


async def test_transaction_safety_rollback(
    client: AsyncClient, auth_headers: dict, setup_job_and_resume: tuple[str, str], db_session
):
    """Test transaction safety: if committing updates fails, timeline event is not created and status is not changed."""
    from fastapi import HTTPException
    from app.users.models import User
    from app.applications.service import ApplicationTrackingService

    job_id, resume_version_id = setup_job_and_resume

    # Retrieve the user to get their ID
    user = (await db_session.execute(select(User).where(User.email == "appuser@example.com"))).scalar_one()
    user_id = user.id

    service = ApplicationTrackingService(db_session)

    # Begin nested transaction 1 to scope creation
    nested1 = await db_session.begin_nested()

    # Create the application directly using the service
    app = await service.create_application(user_id, {
        "job_id": UUID(job_id),
        "resume_version_id": UUID(resume_version_id),
        "status": "draft",
    })
    app_id = app.id

    # Begin nested transaction 2 to scope the status update
    nested2 = await db_session.begin_nested()

    # Mock the db commit to raise an error during status update
    async def mock_commit():
        raise Exception("Mock DB Failure")

    # Mock rollback to roll back only nested2 (the savepoint)
    async def mock_rollback():
        await nested2.rollback()

    with patch.object(db_session, "commit", side_effect=mock_commit), \
         patch.object(db_session, "rollback", side_effect=mock_rollback):
        with pytest.raises(HTTPException) as exc_info:
            await service.update_status(user_id, app_id, "saved")
        assert exc_info.value.status_code == 500


    # Access DB directly using the database fixture to check that state did not modify
    stmt = select(JobApplication).where(JobApplication.id == app_id)
    app_db = (await db_session.execute(stmt)).scalar_one()
    assert app_db.status == "draft"  # rolled back

    # Verify timeline only has 1 event (created)
    stmt_timeline = select(ApplicationTimelineEvent).where(ApplicationTimelineEvent.application_id == app_id)
    events = (await db_session.execute(stmt_timeline)).scalars().all()
    assert len(events) == 1


async def test_job_snapshot_preservation(
    client: AsyncClient, auth_headers: dict, setup_job_and_resume: tuple[str, str], db_session
):
    """Test that the application preserves original job details even if the job record changes or is updated."""
    job_id, resume_version_id = setup_job_and_resume

    # Create application
    create_resp = await client.post("/api/v1/applications", json={
        "job_id": job_id,
        "resume_version_id": resume_version_id,
        "status": "draft",
    }, headers=auth_headers)
    assert create_resp.status_code == 201
    app_id = create_resp.json()["id"]

    # Modify the original job record in the database directly
    stmt = select(Job).where(Job.id == UUID(job_id))
    job_db = (await db_session.execute(stmt)).scalar_one()
    job_db.title = "Completely New Title"
    job_db.company = "NewCompany"
    await db_session.commit()

    # Fetch the application and verify job_snapshot remains unchanged
    get_resp = await client.get(f"/api/v1/applications/{app_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["job_snapshot"]["title"] == "Python Developer"
    assert data["job_snapshot"]["company"] == "TechInc"


async def test_outcome_type_transitions_and_override(
    client: AsyncClient, auth_headers: dict, setup_job_and_resume: tuple[str, str]
):
    """Test outcome_type transitions automatically with status, and manual override."""
    job_id, resume_version_id = setup_job_and_resume

    # Create application
    create_resp = await client.post("/api/v1/applications", json={
        "job_id": job_id,
        "resume_version_id": resume_version_id,
        "status": "draft",
    }, headers=auth_headers)
    app_id = create_resp.json()["id"]

    # Auto transition: draft -> saved -> applied (no_response)
    await client.patch(f"/api/v1/applications/{app_id}/status", json={"status": "saved"}, headers=auth_headers)
    patch_resp = await client.patch(f"/api/v1/applications/{app_id}/status", json={"status": "applied"}, headers=auth_headers)
    assert patch_resp.json()["outcome_type"] == "no_response"

    # Auto transition: applied -> in_review (no_response)
    patch_resp = await client.patch(f"/api/v1/applications/{app_id}/status", json={"status": "in_review"}, headers=auth_headers)
    assert patch_resp.json()["outcome_type"] == "no_response"

    # Auto transition: in_review -> assessment (no_response) -> interview (interviewed)
    await client.patch(f"/api/v1/applications/{app_id}/status", json={"status": "assessment"}, headers=auth_headers)
    patch_resp = await client.patch(f"/api/v1/applications/{app_id}/status", json={"status": "interview"}, headers=auth_headers)
    assert patch_resp.json()["outcome_type"] == "interviewed"

    # Auto transition: interview -> offer (offered)
    patch_resp = await client.patch(f"/api/v1/applications/{app_id}/status", json={"status": "offer"}, headers=auth_headers)
    assert patch_resp.json()["outcome_type"] == "offered"

    # Manual override to accepted (status stays 'offer')
    patch_resp = await client.patch(
        f"/api/v1/applications/{app_id}/status",
        json={"status": "offer", "outcome_type": "accepted"},
        headers=auth_headers
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "offer"
    assert patch_resp.json()["outcome_type"] == "accepted"

