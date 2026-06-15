import pytest
import pytest_asyncio
from uuid import UUID
from unittest.mock import MagicMock, patch
from httpx import AsyncClient
from sqlalchemy import select

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
        "email": "resumeuser@example.com",
        "password": "strongpassword123",
        "full_name": "Resume User",
    }
    await client.post("/api/v1/auth/register", json=register_payload)
    
    login_payload = {
        "email": "resumeuser@example.com",
        "password": "strongpassword123",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    data = response.json()
    token = data["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_upload_first_resume(client: AsyncClient, auth_headers: dict):
    # Upload first PDF file
    files = {"file": ("my_resume.pdf", b"mock pdf content", "application/pdf")}
    response = await client.post("/api/v1/resumes/upload", files=files, headers=auth_headers)
    assert response.status_code == 201
    
    data = response.json()
    assert "id" in data
    assert data["version_number"] == 1
    assert data["original_filename"] == "my_resume.pdf"
    assert "storage_path" in data
    assert data["mime_type"] == "application/pdf"
    assert data["upload_source"] == "upload"

    profile_id = data["profile_id"]
    
    # Verify profile is created
    profiles_response = await client.get("/api/v1/resumes", headers=auth_headers)
    assert profiles_response.status_code == 200
    profiles = profiles_response.json()
    assert len(profiles) == 1
    assert profiles[0]["id"] == profile_id
    assert profiles[0]["name"] == "my_resume.pdf"
    assert profiles[0]["active_version_id"] == data["id"]
    assert profiles[0]["version_count"] == 1


async def test_upload_subsequent_versions(client: AsyncClient, auth_headers: dict):
    # Upload first version
    files = {"file": ("my_resume.pdf", b"mock pdf v1", "application/pdf")}
    v1_response = await client.post("/api/v1/resumes/upload", files=files, headers=auth_headers)
    assert v1_response.status_code == 201
    v1_data = v1_response.json()
    profile_id = v1_data["profile_id"]

    # Upload second version (DOCX)
    files = {"file": ("my_resume_v2.docx", b"mock docx v2 content", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    v2_response = await client.post("/api/v1/resumes/upload", files=files, headers=auth_headers)
    assert v2_response.status_code == 201
    v2_data = v2_response.json()
    
    assert v2_data["profile_id"] == profile_id
    assert v2_data["version_number"] == 2
    assert v2_data["original_filename"] == "my_resume_v2.docx"

    # Get profile details
    profile_response = await client.get(f"/api/v1/resumes/{profile_id}", headers=auth_headers)
    assert profile_response.status_code == 200
    profile = profile_response.json()
    assert profile["version_count"] == 2
    assert profile["active_version_id"] == v2_data["id"]

    # Get version list
    versions_response = await client.get(f"/api/v1/resumes/{profile_id}/versions", headers=auth_headers)
    assert versions_response.status_code == 200
    versions = versions_response.json()
    assert len(versions) == 2
    assert versions[0]["version_number"] == 2
    assert versions[1]["version_number"] == 1


async def test_active_version_switching(client: AsyncClient, auth_headers: dict):
    # Upload v1
    files_v1 = {"file": ("resume.pdf", b"content v1", "application/pdf")}
    v1_data = (await client.post("/api/v1/resumes/upload", files=files_v1, headers=auth_headers)).json()
    profile_id = v1_data["profile_id"]
    v1_id = v1_data["id"]

    # Upload v2
    files_v2 = {"file": ("resume.pdf", b"content v2", "application/pdf")}
    v2_data = (await client.post("/api/v1/resumes/upload", files=files_v2, headers=auth_headers)).json()
    v2_id = v2_data["id"]

    # Verify initial active version is v2
    profile = (await client.get(f"/api/v1/resumes/{profile_id}", headers=auth_headers)).json()
    assert profile["active_version_id"] == v2_id

    # Switch active version to v1
    activate_payload = {"version_id": v1_id}
    activate_response = await client.post(
        f"/api/v1/resumes/{profile_id}/activate-version",
        json=activate_payload,
        headers=auth_headers
    )
    assert activate_response.status_code == 200
    assert activate_response.json()["active_version_id"] == v1_id

    # Verify active version persists in profile detail
    profile = (await client.get(f"/api/v1/resumes/{profile_id}", headers=auth_headers)).json()
    assert profile["active_version_id"] == v1_id


async def test_invalid_file_extension(client: AsyncClient, auth_headers: dict):
    # Upload txt file (invalid)
    files = {"file": ("unsupported.txt", b"plain text", "text/plain")}
    response = await client.post("/api/v1/resumes/upload", files=files, headers=auth_headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "Only PDF and DOCX files are allowed."


async def test_file_size_exceeded(client: AsyncClient, auth_headers: dict):
    # Upload large file (exceeding 5 MB limit)
    large_content = b"x" * (5 * 1024 * 1024 + 1)
    files = {"file": ("large.pdf", large_content, "application/pdf")}
    response = await client.post("/api/v1/resumes/upload", files=files, headers=auth_headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "File size exceeds the 5 MB limit."


async def test_parse_pdf_resume(client: AsyncClient, auth_headers: dict, mock_boto3):
    # 1. Upload a resume
    files = {"file": ("my_resume.pdf", b"pdf bytes content", "application/pdf")}
    upload_res = await client.post("/api/v1/resumes/upload", files=files, headers=auth_headers)
    assert upload_res.status_code == 201
    version_id = upload_res.json()["id"]

    # 2. Setup mock S3 download
    mock_boto3.get_object.return_value = {
        "Body": MagicMock(read=lambda: b"pdf bytes content")
    }

    # 3. Mock pdfplumber.open
    with patch("pdfplumber.open") as mock_pdf_open:
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = (
            "John Doe\njohndoe@example.com\n+123456789\n"
            "Education\nUniversity of Tech\n"
            "Experience\nSoftware Engineer at Company\n"
            "Skills\nPython, FastAPI, Postgres\n"
            "Certifications\nAWS Solutions Architect"
        )
        mock_pdf.pages = [mock_page]
        mock_pdf_open.return_value.__enter__.return_value = mock_pdf

        # Trigger parse
        parse_res = await client.post(f"/api/v1/resumes/{version_id}/parse", headers=auth_headers)
        assert parse_res.status_code == 200

    # 4. Retrieve parsed data
    parsed_res = await client.get(f"/api/v1/resumes/{version_id}/parsed", headers=auth_headers)
    assert parsed_res.status_code == 200
    parsed_data = parsed_res.json()
    
    assert parsed_data["contact_info"]["name"] == "John Doe"
    assert parsed_data["contact_info"]["email"] == "johndoe@example.com"
    assert parsed_data["contact_info"]["phone"] == "+123456789"
    assert "University of Tech" in parsed_data["education"]
    assert "Software Engineer at Company" in parsed_data["experience"]
    assert "Python" in parsed_data["skills"]
    assert "AWS Solutions Architect" in parsed_data["certifications"]


async def test_parse_docx_resume(client: AsyncClient, auth_headers: dict, mock_boto3):
    # 1. Upload a resume
    files = {"file": ("my_resume.docx", b"docx bytes content", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    upload_res = await client.post("/api/v1/resumes/upload", files=files, headers=auth_headers)
    assert upload_res.status_code == 201
    version_id = upload_res.json()["id"]

    # 2. Setup mock S3 download
    mock_boto3.get_object.return_value = {
        "Body": MagicMock(read=lambda: b"docx bytes content")
    }

    # 3. Mock python-docx Document
    with patch("app.resumes.service.Document") as mock_doc_class:
        mock_doc = MagicMock()
        p1 = MagicMock(text="Jane Doe\njanedoe@example.com\n+987654321")
        p2 = MagicMock(text="Skills\nPython, React, TypeScript")
        mock_doc.paragraphs = [p1, p2]
        mock_doc_class.return_value = mock_doc

        # Trigger parse
        parse_res = await client.post(f"/api/v1/resumes/{version_id}/parse", headers=auth_headers)
        assert parse_res.status_code == 200

    # 4. Retrieve parsed data
    parsed_res = await client.get(f"/api/v1/resumes/{version_id}/parsed", headers=auth_headers)
    assert parsed_res.status_code == 200
    parsed_data = parsed_res.json()
    
    assert parsed_data["contact_info"]["name"] == "Jane Doe"
    assert parsed_data["contact_info"]["email"] == "janedoe@example.com"
    assert "Python" in parsed_data["skills"]


async def test_unparsed_retrieve_fails(client: AsyncClient, auth_headers: dict):
    # 1. Upload a resume
    files = {"file": ("my_resume.pdf", b"pdf content", "application/pdf")}
    upload_res = await client.post("/api/v1/resumes/upload", files=files, headers=auth_headers)
    version_id = upload_res.json()["id"]

    # 2. Get parsed fields without calling parse first
    parsed_res = await client.get(f"/api/v1/resumes/{version_id}/parsed", headers=auth_headers)
    assert parsed_res.status_code == 400
    assert "has not been parsed yet" in parsed_res.json()["detail"]


async def test_invalid_parsing_format(client: AsyncClient, auth_headers: dict):
    response = await client.post(f"/api/v1/resumes/00000000-0000-0000-0000-000000000000/parse", headers=auth_headers)
    assert response.status_code == 404


async def test_parse_soft_deleted_resume_fails(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    # 1. Upload a resume
    files = {"file": ("my_resume.pdf", b"pdf content", "application/pdf")}
    upload_res = await client.post("/api/v1/resumes/upload", files=files, headers=auth_headers)
    assert upload_res.status_code == 201
    res_data = upload_res.json()
    version_id = res_data["id"]
    profile_id = res_data["profile_id"]

    # 2. Soft delete the profile in the database
    from app.resumes.models import ResumeProfile
    stmt = select(ResumeProfile).where(ResumeProfile.id == UUID(profile_id))
    profile = (await db_session.execute(stmt)).scalar_one()
    profile.is_deleted = True
    await db_session.commit()

    # 3. Try parsing, should return 404
    parse_res = await client.post(f"/api/v1/resumes/{version_id}/parse", headers=auth_headers)
    assert parse_res.status_code == 404


async def test_parse_download_failure_status(client: AsyncClient, auth_headers: dict, db_session: AsyncSession, mock_boto3):
    # 1. Upload a resume
    files = {"file": ("my_resume.pdf", b"pdf content", "application/pdf")}
    upload_res = await client.post("/api/v1/resumes/upload", files=files, headers=auth_headers)
    assert upload_res.status_code == 201
    version_id = upload_res.json()["id"]

    # 2. Mock MinIO download failure
    mock_boto3.get_object.side_effect = Exception("S3 bucket connection timed out")

    # 3. Parse, should return 500
    parse_res = await client.post(f"/api/v1/resumes/{version_id}/parse", headers=auth_headers)
    assert parse_res.status_code == 500
    assert "Failed to download" in parse_res.json()["detail"]

    # 4. Check status is updated to error
    from app.resumes.models import ResumeVersion
    stmt = select(ResumeVersion).where(ResumeVersion.id == UUID(version_id))
    db_session.expire_all()
    version = (await db_session.execute(stmt)).scalar_one()
    assert version.status == "error"


async def test_parse_malformed_file_status(client: AsyncClient, auth_headers: dict, db_session: AsyncSession, mock_boto3):
    # 1. Upload a resume
    files = {"file": ("my_resume.pdf", b"pdf content", "application/pdf")}
    upload_res = await client.post("/api/v1/resumes/upload", files=files, headers=auth_headers)
    assert upload_res.status_code == 201
    version_id = upload_res.json()["id"]

    # 2. Setup mock S3 download
    mock_boto3.get_object.return_value = {
        "Body": MagicMock(read=lambda: b"malformed pdf content")
    }

    # 3. Mock pdfplumber.open to raise exception
    with patch("pdfplumber.open", side_effect=Exception("PDF header signature not found")):
        # Parse, should return 422
        parse_res = await client.post(f"/api/v1/resumes/{version_id}/parse", headers=auth_headers)
        assert parse_res.status_code == 422
        assert "Error extracting text" in parse_res.json()["detail"]

    # 4. Check status is updated to error
    from app.resumes.models import ResumeVersion
    stmt = select(ResumeVersion).where(ResumeVersion.id == UUID(version_id))
    db_session.expire_all()
    version = (await db_session.execute(stmt)).scalar_one()
    assert version.status == "error"


async def test_unauthorized_user_cannot_parse_resume(client: AsyncClient, auth_headers: dict):
    # 1. Upload a resume under User 1
    files = {"file": ("my_resume.pdf", b"pdf content", "application/pdf")}
    upload_res = await client.post("/api/v1/resumes/upload", files=files, headers=auth_headers)
    assert upload_res.status_code == 201
    version_id = upload_res.json()["id"]

    # 2. Create another user and login
    register_payload = {
        "email": "attacker@example.com",
        "password": "attackerpassword123",
        "full_name": "Attacker User",
    }
    await client.post("/api/v1/auth/register", json=register_payload)
    login_response = await client.post("/api/v1/auth/login", json={
        "email": "attacker@example.com",
        "password": "attackerpassword123",
    })
    attacker_token = login_response.json()["access_token"]
    attacker_headers = {"Authorization": f"Bearer {attacker_token}"}

    # 3. Attacker tries to parse User 1's resume version
    parse_res = await client.post(f"/api/v1/resumes/{version_id}/parse", headers=attacker_headers)
    assert parse_res.status_code == 404

    # 4. Attacker tries to access User 1's parsed data
    parsed_res = await client.get(f"/api/v1/resumes/{version_id}/parsed", headers=attacker_headers)
    assert parsed_res.status_code == 404


async def test_ats_generation_success(client: AsyncClient, auth_headers: dict, mock_boto3, db_session: AsyncSession):
    # 1. Upload a resume
    files = {"file": ("my_resume.pdf", b"pdf content", "application/pdf")}
    upload_res = await client.post("/api/v1/resumes/upload", files=files, headers=auth_headers)
    version_id = upload_res.json()["id"]

    # 2. Mock S3 download & text parsing
    mock_boto3.get_object.return_value = {
        "Body": MagicMock(read=lambda: b"pdf content")
    }

    with patch("pdfplumber.open") as mock_pdf_open:
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = (
            "John Doe\nPython Developer\n"
            "Education\nBachelor of Science in CS\n"
            "Experience\nPython Developer from 2020 to 2024\n"
            "Skills\nPython, FastAPI, Docker\n"
        )
        mock_pdf.pages = [mock_page]
        mock_pdf_open.return_value.__enter__.return_value = mock_pdf

        # Trigger text extraction & structured parsing
        await client.post(f"/api/v1/resumes/{version_id}/parse", headers=auth_headers)

    # 3. Call ATS Scoring endpoint
    jd_text = (
        "We are looking for a Python Developer with 3 years of experience.\n"
        "Requirements:\n"
        "Must have Python, FastAPI, and Kubernetes.\n"
        "Preferred: Docker and AWS Certified.\n"
        "Bachelor's degree required."
    )
    score_payload = {"job_description": jd_text}
    score_res = await client.post(f"/api/v1/resumes/{version_id}/ats-score", json=score_payload, headers=auth_headers)
    assert score_res.status_code == 200
    score_data = score_res.json()

    assert "ats_score" in score_data
    assert "keyword_score" in score_data
    assert "skills_score" in score_data
    assert "experience_score" in score_data
    assert "education_score" in score_data
    assert "missing_keywords" in score_data
    assert "matched_keywords" in score_data
    assert "recommendations" in score_data
    assert "matched_skills" in score_data
    assert "missing_skills" in score_data
    assert "resume_strengths" in score_data
    assert "resume_weaknesses" in score_data
    assert "matched_sections" in score_data
    assert len(score_data["matched_keywords"]) > 0
    assert len(score_data["recommendations"]) > 0
    assert len(score_data["matched_skills"]) > 0
    assert len(score_data["resume_strengths"]) > 0
    assert len(score_data["matched_sections"]) > 0

    # 4. Fetch history and verify it is returned
    history_res = await client.get(f"/api/v1/resumes/{version_id}/ats-history", headers=auth_headers)
    assert history_res.status_code == 200
    history_data = history_res.json()
    assert len(history_data) == 1
    assert history_data[0]["id"] == score_data["id"]


async def test_ats_cache_reuse(client: AsyncClient, auth_headers: dict, mock_boto3, db_session: AsyncSession):
    # 1. Upload & parse a resume
    files = {"file": ("my_resume.pdf", b"pdf content", "application/pdf")}
    upload_res = await client.post("/api/v1/resumes/upload", files=files, headers=auth_headers)
    version_id = upload_res.json()["id"]

    mock_boto3.get_object.return_value = {
        "Body": MagicMock(read=lambda: b"pdf content")
    }
    with patch("pdfplumber.open") as mock_pdf_open:
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Python developer.\nSkills\nPython, FastAPI"
        mock_pdf.pages = [mock_page]
        mock_pdf_open.return_value.__enter__.return_value = mock_pdf
        await client.post(f"/api/v1/resumes/{version_id}/parse", headers=auth_headers)

    # 2. Run ATS Analysis twice with same JD
    jd_text = "Python, FastAPI developer with 2 years of experience."
    score_payload = {"job_description": jd_text}
    
    # First call
    res1 = await client.post(f"/api/v1/resumes/{version_id}/ats-score", json=score_payload, headers=auth_headers)
    assert res1.status_code == 200
    id1 = res1.json()["id"]

    # Second call (should hit cache)
    res2 = await client.post(f"/api/v1/resumes/{version_id}/ats-score", json=score_payload, headers=auth_headers)
    assert res2.status_code == 200
    id2 = res2.json()["id"]

    # Verify ID is exactly identical (cache reuse)
    assert id1 == id2

    # Verify database has exactly one analysis record
    from app.resumes.models import ATSAnalysis
    stmt = select(ATSAnalysis).where(ATSAnalysis.resume_version_id == UUID(version_id))
    db_session.expire_all()
    records = (await db_session.execute(stmt)).scalars().all()
    assert len(records) == 1


async def test_ats_ownership_protection(client: AsyncClient, auth_headers: dict, mock_boto3):
    # 1. Upload a resume under User 1
    files = {"file": ("my_resume.pdf", b"pdf content", "application/pdf")}
    upload_res = await client.post("/api/v1/resumes/upload", files=files, headers=auth_headers)
    version_id = upload_res.json()["id"]

    # 2. Login as another user (Attacker)
    register_payload = {
        "email": "attacker2@example.com",
        "password": "password123",
        "full_name": "Attacker User 2",
    }
    await client.post("/api/v1/auth/register", json=register_payload)
    login_response = await client.post("/api/v1/auth/login", json={
        "email": "attacker2@example.com",
        "password": "password123",
    })
    attacker_headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}

    # 3. Attacker tries to parse or compute ATS score
    score_res = await client.post(
        f"/api/v1/resumes/{version_id}/ats-score",
        json={"job_description": "Python developer"},
        headers=attacker_headers
    )
    assert score_res.status_code == 404

    # 4. Attacker tries to get ATS history
    history_res = await client.get(f"/api/v1/resumes/{version_id}/ats-history", headers=attacker_headers)
    assert history_res.status_code == 404


async def test_ats_soft_deleted_protection(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    # 1. Upload a resume
    files = {"file": ("my_resume.pdf", b"pdf content", "application/pdf")}
    upload_res = await client.post("/api/v1/resumes/upload", files=files, headers=auth_headers)
    res_data = upload_res.json()
    version_id = res_data["id"]
    profile_id = res_data["profile_id"]

    # 2. Soft delete the parent profile
    from app.resumes.models import ResumeProfile
    stmt = select(ResumeProfile).where(ResumeProfile.id == UUID(profile_id))
    profile = (await db_session.execute(stmt)).scalar_one()
    profile.is_deleted = True
    await db_session.commit()

    # 3. Try to compute ATS score, should return 404
    score_res = await client.post(
        f"/api/v1/resumes/{version_id}/ats-score",
        json={"job_description": "Python developer"},
        headers=auth_headers
    )
    assert score_res.status_code == 404


async def test_ats_large_job_description_rejected(client: AsyncClient, auth_headers: dict):
    # 1. Upload a resume
    files = {"file": ("my_resume.pdf", b"pdf content", "application/pdf")}
    upload_res = await client.post("/api/v1/resumes/upload", files=files, headers=auth_headers)
    version_id = upload_res.json()["id"]

    # 2. Try to score with a very large job description (exceeding 50,000 characters)
    large_jd = "Python " * 10000 # 70000 chars
    score_res = await client.post(
        f"/api/v1/resumes/{version_id}/ats-score",
        json={"job_description": large_jd},
        headers=auth_headers
    )
    assert score_res.status_code in [400, 422]

