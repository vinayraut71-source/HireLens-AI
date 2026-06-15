"""Sprint 5 Integration Tests: Job CRUD + Intelligent Job Matching."""
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
        "email": "jobuser@example.com",
        "password": "strongpassword123",
        "full_name": "Job User",
    }
    await client.post("/api/v1/auth/register", json=register_payload)
    login_payload = {
        "email": "jobuser@example.com",
        "password": "strongpassword123",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    data = response.json()
    return {"Authorization": f"Bearer {data['access_token']}"}


@pytest_asyncio.fixture
async def second_auth_headers(client: AsyncClient) -> dict:
    """Register and login a second user for ownership tests."""
    register_payload = {
        "email": "jobuser2@example.com",
        "password": "strongpassword123",
        "full_name": "Job User 2",
    }
    await client.post("/api/v1/auth/register", json=register_payload)
    login_payload = {
        "email": "jobuser2@example.com",
        "password": "strongpassword123",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    data = response.json()
    return {"Authorization": f"Bearer {data['access_token']}"}


JOB_DESCRIPTION_PYTHON = """
Senior Python Developer

Requirements:
- 5+ years of experience in software development
- Strong proficiency in Python, Django, FastAPI
- Experience with PostgreSQL, Redis
- Bachelor's degree in Computer Science or equivalent
- Familiarity with Docker, Kubernetes, CI/CD
- Experience with REST API design

Preferred:
- Experience with machine learning or NLP is a plus
- AWS or GCP cloud experience preferred
"""

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


# =============================================================================
# Job CRUD Tests
# =============================================================================


async def test_create_job(client: AsyncClient, auth_headers: dict):
    """Test creating a new job."""
    payload = {
        "title": "Senior Python Developer",
        "description": JOB_DESCRIPTION_PYTHON,
        "company": "TechCorp",
        "location": "San Francisco, CA",
        "remote_type": "hybrid",
    }
    response = await client.post("/api/v1/jobs", json=payload, headers=auth_headers)
    assert response.status_code == 201

    data = response.json()
    assert data["title"] == "Senior Python Developer"
    assert data["company"] == "TechCorp"
    assert data["is_saved"] is True
    assert "id" in data
    assert "created_at" in data


async def test_list_jobs(client: AsyncClient, auth_headers: dict):
    """Test listing user's jobs."""
    # Create two jobs
    for title in ["Job A", "Job B"]:
        await client.post("/api/v1/jobs", json={
            "title": title,
            "description": "Some description for the job.",
        }, headers=auth_headers)

    response = await client.get("/api/v1/jobs", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


async def test_get_job_detail(client: AsyncClient, auth_headers: dict):
    """Test getting a specific job."""
    create_resp = await client.post("/api/v1/jobs", json={
        "title": "Detail Test Job",
        "description": "Detailed description.",
    }, headers=auth_headers)
    job_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/jobs/{job_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["title"] == "Detail Test Job"


async def test_update_job(client: AsyncClient, auth_headers: dict):
    """Test updating a job."""
    create_resp = await client.post("/api/v1/jobs", json={
        "title": "Update Test Job",
        "description": "Original description.",
    }, headers=auth_headers)
    job_id = create_resp.json()["id"]

    response = await client.patch(f"/api/v1/jobs/{job_id}", json={
        "title": "Updated Job Title",
        "is_saved": False,
    }, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Job Title"
    assert response.json()["is_saved"] is False


async def test_delete_job(client: AsyncClient, auth_headers: dict):
    """Test soft-deleting a job."""
    create_resp = await client.post("/api/v1/jobs", json={
        "title": "Delete Test Job",
        "description": "To be deleted.",
    }, headers=auth_headers)
    job_id = create_resp.json()["id"]

    delete_resp = await client.delete(f"/api/v1/jobs/{job_id}", headers=auth_headers)
    assert delete_resp.status_code == 204

    # Verify it's no longer accessible
    get_resp = await client.get(f"/api/v1/jobs/{job_id}", headers=auth_headers)
    assert get_resp.status_code == 404


async def test_job_ownership_isolation(client: AsyncClient, auth_headers: dict, second_auth_headers: dict):
    """Test that user 2 cannot access user 1's jobs."""
    create_resp = await client.post("/api/v1/jobs", json={
        "title": "Private Job",
        "description": "This is private.",
    }, headers=auth_headers)
    job_id = create_resp.json()["id"]

    # User 2 should not see user 1's job
    get_resp = await client.get(f"/api/v1/jobs/{job_id}", headers=second_auth_headers)
    assert get_resp.status_code == 404


# =============================================================================
# Job Matching Tests
# =============================================================================


@pytest_asyncio.fixture
async def parsed_resume_version_id(client: AsyncClient, auth_headers: dict, mock_boto3) -> str:
    """Upload and parse a resume, return the version ID."""
    # Create a mock PDF with resume-like content
    resume_text = """John Doe
john.doe@email.com
+1-555-123-4567

Experience
Senior Developer at TechCo 2019 - Present
- Built REST APIs using Python, Django, FastAPI
- Managed PostgreSQL databases and Redis caches
- Deployed with Docker and Kubernetes

Junior Developer at StartupInc 2016 - 2019
- Developed web applications using Python and Flask
- Worked with MySQL and MongoDB

Education
Bachelor of Science in Computer Science
University of Technology, 2016

Skills
Python, Django, FastAPI, PostgreSQL, Redis, Docker, Kubernetes, REST API, Git, CI/CD, SQL, Linux

Certifications
AWS Certified Solutions Architect
"""

    # Mock the storage service to return our resume text when downloaded
    mock_boto3.get_object.return_value = {
        "Body": MagicMock(read=lambda: resume_text.encode("utf-8"))
    }

    # Upload
    files = {"file": ("resume.pdf", b"mock pdf content", "application/pdf")}
    upload_resp = await client.post("/api/v1/resumes/upload", files=files, headers=auth_headers)
    assert upload_resp.status_code == 201
    version_id = upload_resp.json()["id"]

    # Parse — mock pdfplumber to return our resume text
    with patch("app.resumes.service.pdfplumber") as mock_pdf:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = resume_text
        mock_pdf_obj = MagicMock()
        mock_pdf_obj.pages = [mock_page]
        mock_pdf_obj.__enter__ = MagicMock(return_value=mock_pdf_obj)
        mock_pdf_obj.__exit__ = MagicMock(return_value=False)
        mock_pdf.open.return_value = mock_pdf_obj

        parse_resp = await client.post(f"/api/v1/resumes/{version_id}/parse", headers=auth_headers)
        assert parse_resp.status_code == 200

    return version_id


async def test_job_match_success(client: AsyncClient, auth_headers: dict, parsed_resume_version_id: str):
    """Test creating a successful job match."""
    # Create a job
    job_resp = await client.post("/api/v1/jobs", json={
        "title": "Senior Python Developer",
        "description": JOB_DESCRIPTION_PYTHON,
        "company": "TechCorp",
    }, headers=auth_headers)
    assert job_resp.status_code == 201
    job_id = job_resp.json()["id"]

    # Match resume against job
    match_resp = await client.post(f"/api/v1/jobs/{job_id}/match", json={
        "resume_version_id": parsed_resume_version_id,
    }, headers=auth_headers)
    assert match_resp.status_code == 201

    data = match_resp.json()
    assert "id" in data
    assert data["job_id"] == job_id
    assert data["resume_version_id"] == parsed_resume_version_id
    assert 0 <= data["overall_match_score"] <= 100
    assert 0 <= data["skills_match_score"] <= 100
    assert 0 <= data["experience_match_score"] <= 100
    assert 0 <= data["education_match_score"] <= 100
    assert 0 <= data["keyword_match_score"] <= 100
    assert isinstance(data["matched_skills"], list)
    assert isinstance(data["missing_skills"], list)
    assert isinstance(data["strengths"], list)
    assert isinstance(data["weaknesses"], list)
    assert isinstance(data["fit_summary"], str)
    assert len(data["fit_summary"]) > 0
    assert isinstance(data["improvement_actions"], list)
    assert "created_at" in data


async def test_job_match_deterministic(client: AsyncClient, auth_headers: dict, parsed_resume_version_id: str):
    """Test that identical inputs produce identical match outputs (idempotent caching)."""
    job_resp = await client.post("/api/v1/jobs", json={
        "title": "Python Dev Role",
        "description": JOB_DESCRIPTION_PYTHON,
    }, headers=auth_headers)
    job_id = job_resp.json()["id"]

    # First match
    match1_resp = await client.post(f"/api/v1/jobs/{job_id}/match", json={
        "resume_version_id": parsed_resume_version_id,
    }, headers=auth_headers)
    assert match1_resp.status_code == 201
    data1 = match1_resp.json()

    # Second match with same inputs — should return cached result
    match2_resp = await client.post(f"/api/v1/jobs/{job_id}/match", json={
        "resume_version_id": parsed_resume_version_id,
    }, headers=auth_headers)
    assert match2_resp.status_code == 201
    data2 = match2_resp.json()

    # Identical outputs
    assert data1["id"] == data2["id"]
    assert data1["overall_match_score"] == data2["overall_match_score"]
    assert data1["skills_match_score"] == data2["skills_match_score"]
    assert data1["matched_skills"] == data2["matched_skills"]
    assert data1["fit_summary"] == data2["fit_summary"]


async def test_job_match_different_jds_produce_different_scores(
    client: AsyncClient, auth_headers: dict, parsed_resume_version_id: str
):
    """Test that different job descriptions produce different match scores."""
    # Job 1: Python-focused
    job1_resp = await client.post("/api/v1/jobs", json={
        "title": "Python Dev",
        "description": JOB_DESCRIPTION_PYTHON,
    }, headers=auth_headers)
    job1_id = job1_resp.json()["id"]

    # Job 2: Java-focused
    job2_resp = await client.post("/api/v1/jobs", json={
        "title": "Java Dev",
        "description": JOB_DESCRIPTION_JAVA,
    }, headers=auth_headers)
    job2_id = job2_resp.json()["id"]

    match1 = await client.post(f"/api/v1/jobs/{job1_id}/match", json={
        "resume_version_id": parsed_resume_version_id,
    }, headers=auth_headers)
    match2 = await client.post(f"/api/v1/jobs/{job2_id}/match", json={
        "resume_version_id": parsed_resume_version_id,
    }, headers=auth_headers)

    data1 = match1.json()
    data2 = match2.json()

    # Python resume should score higher against Python JD than Java JD
    assert data1["overall_match_score"] != data2["overall_match_score"]
    assert data1["skills_match_score"] >= data2["skills_match_score"]


async def test_list_matches(client: AsyncClient, auth_headers: dict, parsed_resume_version_id: str):
    """Test listing all job matches."""
    # Create a job and match
    job_resp = await client.post("/api/v1/jobs", json={
        "title": "List Match Test",
        "description": JOB_DESCRIPTION_PYTHON,
    }, headers=auth_headers)
    job_id = job_resp.json()["id"]

    await client.post(f"/api/v1/jobs/{job_id}/match", json={
        "resume_version_id": parsed_resume_version_id,
    }, headers=auth_headers)

    # List matches
    list_resp = await client.get("/api/v1/jobs/matches/list", headers=auth_headers)
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "overall_match_score" in data[0]
    assert "fit_summary" in data[0]


async def test_get_match_detail(client: AsyncClient, auth_headers: dict, parsed_resume_version_id: str):
    """Test getting a specific match result."""
    job_resp = await client.post("/api/v1/jobs", json={
        "title": "Detail Match Test",
        "description": JOB_DESCRIPTION_PYTHON,
    }, headers=auth_headers)
    job_id = job_resp.json()["id"]

    match_resp = await client.post(f"/api/v1/jobs/{job_id}/match", json={
        "resume_version_id": parsed_resume_version_id,
    }, headers=auth_headers)
    match_id = match_resp.json()["id"]

    detail_resp = await client.get(f"/api/v1/jobs/matches/{match_id}", headers=auth_headers)
    assert detail_resp.status_code == 200
    data = detail_resp.json()
    assert data["id"] == match_id
    assert "improvement_actions" in data


async def test_match_ownership_isolation(
    client: AsyncClient, auth_headers: dict, second_auth_headers: dict, parsed_resume_version_id: str
):
    """Test that user 2 cannot access user 1's match results."""
    job_resp = await client.post("/api/v1/jobs", json={
        "title": "Ownership Test Job",
        "description": JOB_DESCRIPTION_PYTHON,
    }, headers=auth_headers)
    job_id = job_resp.json()["id"]

    match_resp = await client.post(f"/api/v1/jobs/{job_id}/match", json={
        "resume_version_id": parsed_resume_version_id,
    }, headers=auth_headers)
    match_id = match_resp.json()["id"]

    # User 2 should not see user 1's match
    get_resp = await client.get(f"/api/v1/jobs/matches/{match_id}", headers=second_auth_headers)
    assert get_resp.status_code == 404


async def test_match_nonexistent_job_returns_404(client: AsyncClient, auth_headers: dict, parsed_resume_version_id: str):
    """Test matching against a non-existent job ID."""
    fake_job_id = "00000000-0000-0000-0000-000000000000"
    resp = await client.post(f"/api/v1/jobs/{fake_job_id}/match", json={
        "resume_version_id": parsed_resume_version_id,
    }, headers=auth_headers)
    assert resp.status_code == 404


async def test_match_nonexistent_resume_returns_404(client: AsyncClient, auth_headers: dict):
    """Test matching with a non-existent resume version ID."""
    job_resp = await client.post("/api/v1/jobs", json={
        "title": "404 Resume Test",
        "description": "Some description.",
    }, headers=auth_headers)
    job_id = job_resp.json()["id"]

    fake_version_id = "00000000-0000-0000-0000-000000000001"
    resp = await client.post(f"/api/v1/jobs/{job_id}/match", json={
        "resume_version_id": fake_version_id,
    }, headers=auth_headers)
    assert resp.status_code == 404


async def test_match_against_deleted_job_returns_404(
    client: AsyncClient, auth_headers: dict, parsed_resume_version_id: str
):
    """Test that matching against a soft-deleted job returns 404."""
    job_resp = await client.post("/api/v1/jobs", json={
        "title": "Deleted Job Test",
        "description": JOB_DESCRIPTION_PYTHON,
    }, headers=auth_headers)
    job_id = job_resp.json()["id"]

    # Delete the job
    del_resp = await client.delete(f"/api/v1/jobs/{job_id}", headers=auth_headers)
    assert del_resp.status_code == 204

    # Match should fail
    match_resp = await client.post(f"/api/v1/jobs/{job_id}/match", json={
        "resume_version_id": parsed_resume_version_id,
    }, headers=auth_headers)
    assert match_resp.status_code == 404


async def test_match_unauthenticated(client: AsyncClient):
    """Test that unauthenticated requests are rejected."""
    fake_job_id = "00000000-0000-0000-0000-000000000000"
    resp = await client.post(f"/api/v1/jobs/{fake_job_id}/match", json={
        "resume_version_id": "00000000-0000-0000-0000-000000000001",
    })
    assert resp.status_code in (401, 403)


async def test_match_score_ranges(client: AsyncClient, auth_headers: dict, parsed_resume_version_id: str):
    """Test that all scores are in the 0-100 range."""
    job_resp = await client.post("/api/v1/jobs", json={
        "title": "Range Test Job",
        "description": JOB_DESCRIPTION_JAVA,  # Java JD against Python resume → lower scores
    }, headers=auth_headers)
    job_id = job_resp.json()["id"]

    match_resp = await client.post(f"/api/v1/jobs/{job_id}/match", json={
        "resume_version_id": parsed_resume_version_id,
    }, headers=auth_headers)
    data = match_resp.json()

    for field in ["overall_match_score", "skills_match_score", "experience_match_score",
                   "education_match_score", "keyword_match_score"]:
        assert 0 <= data[field] <= 100, f"{field}={data[field]} out of range"


# =============================================================================
# Skill Gap Analysis Tests (Sprint 6)
# =============================================================================


async def test_skill_gap_generation_success(
    client: AsyncClient, auth_headers: dict, parsed_resume_version_id: str
):
    """Test generating skill gap analysis for a job match."""
    # Create a Java job (has gaps compared to Python resume)
    job_resp = await client.post("/api/v1/jobs", json={
        "title": "Java Backend Engineer",
        "description": JOB_DESCRIPTION_JAVA,
        "company": "TechCorp",
    }, headers=auth_headers)
    assert job_resp.status_code == 201
    job_id = job_resp.json()["id"]

    # Match resume against job
    match_resp = await client.post(f"/api/v1/jobs/{job_id}/match", json={
        "resume_version_id": parsed_resume_version_id,
    }, headers=auth_headers)
    assert match_resp.status_code == 201
    match_id = match_resp.json()["id"]

    # Generate skill gap analysis
    gap_resp = await client.post(f"/api/v1/jobs/matches/{match_id}/skill-gap", headers=auth_headers)
    assert gap_resp.status_code == 201
    data = gap_resp.json()

    assert data["job_match_id"] == match_id
    assert data["total_gaps"] > 0
    assert data["critical_count"] + data["high_count"] + data["medium_count"] + data["low_count"] == data["total_gaps"]
    assert isinstance(data["gaps"], list)
    assert len(data["gaps"]) == data["total_gaps"]

    # Verify gap details
    gap = data["gaps"][0]
    assert "id" in gap
    assert gap["job_match_id"] == match_id
    assert "missing_skill" in gap
    assert 0 <= gap["importance_score"] <= 100
    assert gap["category"] in ["technical", "soft-skill", "certification", "tool", "domain"]
    assert gap["learning_priority"] in ["critical", "high", "medium", "low"]
    assert "estimated_learning_time" in gap
    assert "recommendation_reason" in gap
    assert "roadmap_priority_score" in gap
    assert 0 <= gap["roadmap_priority_score"] <= 100


async def test_skill_gap_cache_reuse(
    client: AsyncClient, auth_headers: dict, parsed_resume_version_id: str
):
    """Test that consecutive POST requests return cached skill gap analysis."""
    job_resp = await client.post("/api/v1/jobs", json={
        "title": "Java Role",
        "description": JOB_DESCRIPTION_JAVA,
    }, headers=auth_headers)
    job_id = job_resp.json()["id"]

    match_resp = await client.post(f"/api/v1/jobs/{job_id}/match", json={
        "resume_version_id": parsed_resume_version_id,
    }, headers=auth_headers)
    match_id = match_resp.json()["id"]

    # Generate first time
    gap1_resp = await client.post(f"/api/v1/jobs/matches/{match_id}/skill-gap", headers=auth_headers)
    assert gap1_resp.status_code == 201
    data1 = gap1_resp.json()

    # Generate second time — should be identical cached result
    gap2_resp = await client.post(f"/api/v1/jobs/matches/{match_id}/skill-gap", headers=auth_headers)
    assert gap2_resp.status_code == 201
    data2 = gap2_resp.json()

    assert data1["total_gaps"] == data2["total_gaps"]
    assert [g["id"] for g in data1["gaps"]] == [g["id"] for g in data2["gaps"]]


async def test_skill_gap_get_success(
    client: AsyncClient, auth_headers: dict, parsed_resume_version_id: str
):
    """Test getting generated skill gaps."""
    job_resp = await client.post("/api/v1/jobs", json={
        "title": "Java Role",
        "description": JOB_DESCRIPTION_JAVA,
    }, headers=auth_headers)
    job_id = job_resp.json()["id"]

    match_resp = await client.post(f"/api/v1/jobs/{job_id}/match", json={
        "resume_version_id": parsed_resume_version_id,
    }, headers=auth_headers)
    match_id = match_resp.json()["id"]

    # Before generating, GET might be empty or cached. But let's generate first.
    await client.post(f"/api/v1/jobs/matches/{match_id}/skill-gap", headers=auth_headers)

    # Fetch gaps
    get_resp = await client.get(f"/api/v1/jobs/matches/{match_id}/skill-gap", headers=auth_headers)
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["job_match_id"] == match_id
    assert data["total_gaps"] > 0


async def test_skill_gap_ownership_isolation(
    client: AsyncClient, auth_headers: dict, second_auth_headers: dict, parsed_resume_version_id: str
):
    """Test that a user cannot access another user's skill gap analysis."""
    job_resp = await client.post("/api/v1/jobs", json={
        "title": "Java Role",
        "description": JOB_DESCRIPTION_JAVA,
    }, headers=auth_headers)
    job_id = job_resp.json()["id"]

    match_resp = await client.post(f"/api/v1/jobs/{job_id}/match", json={
        "resume_version_id": parsed_resume_version_id,
    }, headers=auth_headers)
    match_id = match_resp.json()["id"]

    # Generate gaps as User 1
    await client.post(f"/api/v1/jobs/matches/{match_id}/skill-gap", headers=auth_headers)

    # User 2 tries to GET
    get_resp = await client.get(f"/api/v1/jobs/matches/{match_id}/skill-gap", headers=second_auth_headers)
    assert get_resp.status_code == 404

    # User 2 tries to POST
    post_resp = await client.post(f"/api/v1/jobs/matches/{match_id}/skill-gap", headers=second_auth_headers)
    assert post_resp.status_code == 404


async def test_skill_gap_invalid_match_id(client: AsyncClient, auth_headers: dict):
    """Test accessing skill gaps for a non-existent match ID."""
    fake_match_id = "00000000-0000-0000-0000-000000000000"
    resp = await client.get(f"/api/v1/jobs/matches/{fake_match_id}/skill-gap", headers=auth_headers)
    assert resp.status_code == 404
