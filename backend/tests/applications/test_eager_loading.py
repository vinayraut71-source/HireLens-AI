"""Sprint 10.5 Fix #2 Integration Tests: Eager loading for JobApplication.timeline_events."""
import pytest
import pytest_asyncio
from unittest.mock import MagicMock, patch
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def mock_boto3():
    with patch("boto3.client") as mock_client:
        mock_s3 = MagicMock()
        mock_client.return_value = mock_s3
        yield mock_s3


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict:
    register_payload = {
        "email": "eager_app_user@example.com",
        "password": "strongpassword123",
        "full_name": "Eager App User",
    }
    await client.post("/api/v1/auth/register", json=register_payload)
    login_payload = {
        "email": "eager_app_user@example.com",
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

    with patch("app.resumes.service.pdfplumber") as mock_pdf:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = resume_text
        mock_pdf_obj = MagicMock()
        mock_pdf_obj.pages = [mock_page]
        mock_pdf_obj.__enter__ = MagicMock(return_value=mock_pdf_obj)
        mock_pdf_obj.__exit__ = MagicMock(return_value=False)
        mock_pdf.open.return_value = mock_pdf_obj
        await client.post(f"/api/v1/resumes/{version_id}/parse", headers=auth_headers)

    job_resp = await client.post("/api/v1/jobs", json={
        "title": "Python Developer",
        "description": "proficient in Python and Django and Docker.",
        "company": "EagerCo",
    }, headers=auth_headers)
    job_id = job_resp.json()["id"]

    return job_id, version_id


async def test_create_application_returns_successfully(
    client: AsyncClient, auth_headers: dict, setup_job_and_resume: tuple[str, str]
):
    """Creating an application should succeed without MissingGreenlet (timeline_events eagerly loaded)."""
    job_id, version_id = setup_job_and_resume
    resp = await client.post("/api/v1/applications", json={
        "job_id": job_id,
        "resume_version_id": version_id,
        "status": "applied",
    }, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "applied"
    assert data["outcome_type"] == "no_response"


async def test_get_application_returns_successfully(
    client: AsyncClient, auth_headers: dict, setup_job_and_resume: tuple[str, str]
):
    """Fetching a single application should succeed without MissingGreenlet."""
    job_id, version_id = setup_job_and_resume
    create_resp = await client.post("/api/v1/applications", json={
        "job_id": job_id,
        "resume_version_id": version_id,
        "status": "draft",
    }, headers=auth_headers)
    app_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/applications/{app_id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == app_id
    assert data["status"] == "draft"


async def test_list_applications_returns_successfully(
    client: AsyncClient, auth_headers: dict, setup_job_and_resume: tuple[str, str]
):
    """Listing applications should succeed without MissingGreenlet."""
    job_id, version_id = setup_job_and_resume
    await client.post("/api/v1/applications", json={
        "job_id": job_id,
        "resume_version_id": version_id,
        "status": "applied",
    }, headers=auth_headers)

    resp = await client.get("/api/v1/applications", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


async def test_timeline_events_accessible_after_create(
    client: AsyncClient, auth_headers: dict, setup_job_and_resume: tuple[str, str]
):
    """Timeline events should be accessible via /timeline endpoint after creating an application."""
    job_id, version_id = setup_job_and_resume
    create_resp = await client.post("/api/v1/applications", json={
        "job_id": job_id,
        "resume_version_id": version_id,
        "status": "applied",
    }, headers=auth_headers)
    app_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/applications/{app_id}/timeline", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["event_type"] == "created"
    assert data[0]["new_status"] == "applied"


async def test_timeline_events_grow_after_status_update(
    client: AsyncClient, auth_headers: dict, setup_job_and_resume: tuple[str, str]
):
    """After a status update, timeline should reflect both creation and transition events."""
    job_id, version_id = setup_job_and_resume
    create_resp = await client.post("/api/v1/applications", json={
        "job_id": job_id,
        "resume_version_id": version_id,
        "status": "draft",
    }, headers=auth_headers)
    app_id = create_resp.json()["id"]

    # Transition draft -> saved
    update_resp = await client.patch(f"/api/v1/applications/{app_id}/status", json={
        "status": "saved",
    }, headers=auth_headers)
    assert update_resp.status_code == 200

    # Verify timeline
    resp = await client.get(f"/api/v1/applications/{app_id}/timeline", headers=auth_headers)
    data = resp.json()
    assert len(data) >= 2
    # Events are ordered newest first
    event_types = [e["event_type"] for e in data]
    assert "created" in event_types
    assert "status_change" in event_types
