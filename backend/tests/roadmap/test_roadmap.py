"""Sprint 7 Integration Tests: Career Roadmap Generator."""
import pytest
import pytest_asyncio
from uuid import UUID
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
    """Register and login a test user, return auth headers."""
    register_payload = {
        "email": "roadmapuser@example.com",
        "password": "strongpassword123",
        "full_name": "Roadmap User",
    }
    await client.post("/api/v1/auth/register", json=register_payload)
    login_payload = {
        "email": "roadmapuser@example.com",
        "password": "strongpassword123",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    data = response.json()
    return {"Authorization": f"Bearer {data['access_token']}"}


@pytest_asyncio.fixture
async def second_auth_headers(client: AsyncClient) -> dict:
    """Register and login a second user for ownership tests."""
    register_payload = {
        "email": "roadmapuser2@example.com",
        "password": "strongpassword123",
        "full_name": "Roadmap User 2",
    }
    await client.post("/api/v1/auth/register", json=register_payload)
    login_payload = {
        "email": "roadmapuser2@example.com",
        "password": "strongpassword123",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    data = response.json()
    return {"Authorization": f"Bearer {data['access_token']}"}


JOB_DESCRIPTION_JAVA = """
Java Backend Engineer

Requirements:
- 3+ years of experience in Java development
- Strong knowledge of Spring Boot, Hibernate
- Experience with MySQL, MongoDB
- Master's degree preferred
- Familiarity with Docker, Kubernetes

Nice to have:
- Experience with React or Angular is a plus
"""


@pytest_asyncio.fixture
async def matched_job_match_id(client: AsyncClient, auth_headers: dict, mock_boto3) -> str:
    """Create a parsed resume, a job, and trigger a match, returning the match ID."""
    resume_text = """John Doe
john.doe@email.com

Experience
Senior Developer at TechCo 2019 - Present
- Built REST APIs using Python, Django, FastAPI
- Managed PostgreSQL databases and Redis caches
- Deployed with Docker

Education
Bachelor of Science in Computer Science

Skills
Python, Django, FastAPI, PostgreSQL, Redis, Docker, Git, CI/CD, SQL
"""
    # Mock storage and PDF parser
    mock_boto3.get_object.return_value = {
        "Body": MagicMock(read=lambda: resume_text.encode("utf-8"))
    }

    files = {"file": ("resume.pdf", b"mock pdf content", "application/pdf")}
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

    # Create Java Job
    job_resp = await client.post("/api/v1/jobs", json={
        "title": "Java Developer",
        "description": JOB_DESCRIPTION_JAVA,
        "company": "EnterpriseCorp",
    }, headers=auth_headers)
    job_id = job_resp.json()["id"]

    # Match
    match_resp = await client.post(f"/api/v1/jobs/{job_id}/match", json={
        "resume_version_id": version_id,
    }, headers=auth_headers)
    
    # Generate skill gaps (this triggers skill gap caching)
    match_id = match_resp.json()["id"]
    await client.post(f"/api/v1/jobs/matches/{match_id}/skill-gap", headers=auth_headers)

    return match_id


# =============================================================================
# Career Roadmap Generator Tests
# =============================================================================


async def test_roadmap_generation_success(
    client: AsyncClient, auth_headers: dict, matched_job_match_id: str
):
    """Test successful career roadmap generation."""
    response = await client.post(
        f"/api/v1/jobs/matches/{matched_job_match_id}/roadmap", headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()

    assert "id" in data
    assert data["job_match_id"] == matched_job_match_id
    assert data["total_estimated_weeks"] > 0
    assert data["roadmap_status"] == "active"
    assert isinstance(data["milestones"], list)
    assert len(data["milestones"]) > 0

    # Verify milestone fields
    milestone = data["milestones"][0]
    assert "id" in milestone
    assert milestone["roadmap_id"] == data["id"]
    assert "skill_gap_id" in milestone
    assert milestone["milestone_order"] == 1
    assert "estimated_weeks" in milestone
    assert milestone["completion_status"] == "pending"


async def test_roadmap_cache_reuse(
    client: AsyncClient, auth_headers: dict, matched_job_match_id: str
):
    """Test that generating multiple times returns the same cached roadmap (idempotency)."""
    resp1 = await client.post(
        f"/api/v1/jobs/matches/{matched_job_match_id}/roadmap", headers=auth_headers
    )
    assert resp1.status_code == 201
    id1 = resp1.json()["id"]

    # Second call should return the exact same cached roadmap
    resp2 = await client.post(
        f"/api/v1/jobs/matches/{matched_job_match_id}/roadmap", headers=auth_headers
    )
    assert resp2.status_code == 201
    id2 = resp2.json()["id"]

    assert id1 == id2


async def test_get_roadmap_success(
    client: AsyncClient, auth_headers: dict, matched_job_match_id: str
):
    """Test getting a generated roadmap."""
    # Generate first
    await client.post(
        f"/api/v1/jobs/matches/{matched_job_match_id}/roadmap", headers=auth_headers
    )

    # Get
    response = await client.get(
        f"/api/v1/jobs/matches/{matched_job_match_id}/roadmap", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["job_match_id"] == matched_job_match_id
    assert len(data["milestones"]) > 0


async def test_roadmap_ownership_protection(
    client: AsyncClient, auth_headers: dict, second_auth_headers: dict, matched_job_match_id: str
):
    """Test that user 2 cannot access user 1's roadmap."""
    # Generate as user 1
    await client.post(
        f"/api/v1/jobs/matches/{matched_job_match_id}/roadmap", headers=auth_headers
    )

    # Try to GET as user 2
    get_resp = await client.get(
        f"/api/v1/jobs/matches/{matched_job_match_id}/roadmap", headers=second_auth_headers
    )
    assert get_resp.status_code == 404

    # Try to POST as user 2
    post_resp = await client.post(
        f"/api/v1/jobs/matches/{matched_job_match_id}/roadmap", headers=second_auth_headers
    )
    assert post_resp.status_code == 404


async def test_milestone_ordering_and_weeks(
    client: AsyncClient, auth_headers: dict, matched_job_match_id: str
):
    """Verify that milestones are ordered by roadmap_priority_score descending and estimated weeks are correct."""
    response = await client.post(
        f"/api/v1/jobs/matches/{matched_job_match_id}/roadmap", headers=auth_headers
    )
    milestones = response.json()["milestones"]

    # Verify orders are sequential (1, 2, 3...)
    orders = [m["milestone_order"] for m in milestones]
    assert orders == list(range(1, len(milestones) + 1))

    # Verify priority scores are sorted descending
    scores = [m["priority_score"] for m in milestones]
    assert scores == sorted(scores, reverse=True)

    # Verify weeks are positive integers
    for m in milestones:
        assert m["estimated_weeks"] in [1, 2, 3, 4]


async def test_milestone_completion_tracking(
    client: AsyncClient, auth_headers: dict, matched_job_match_id: str
):
    """Test updating a milestone's completion status."""
    gen_resp = await client.post(
        f"/api/v1/jobs/matches/{matched_job_match_id}/roadmap", headers=auth_headers
    )
    roadmap_id = gen_resp.json()["id"]
    milestone_id = gen_resp.json()["milestones"][0]["id"]

    # Patch progress to in_progress
    patch_resp1 = await client.patch(
        f"/api/v1/roadmaps/{roadmap_id}/milestones/{milestone_id}",
        json={"completion_status": "in_progress"},
        headers=auth_headers,
    )
    assert patch_resp1.status_code == 200
    assert patch_resp1.json()["completion_status"] == "in_progress"

    # Patch progress to completed
    patch_resp2 = await client.patch(
        f"/api/v1/roadmaps/{roadmap_id}/milestones/{milestone_id}",
        json={"completion_status": "completed"},
        headers=auth_headers,
    )
    assert patch_resp2.status_code == 200
    assert patch_resp2.json()["completion_status"] == "completed"

    # Verify GET reflects completion
    get_resp = await client.get(
        f"/api/v1/jobs/matches/{matched_job_match_id}/roadmap", headers=auth_headers
    )
    assert get_resp.json()["milestones"][0]["completion_status"] == "completed"
