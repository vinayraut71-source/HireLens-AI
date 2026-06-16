import pytest
import pytest_asyncio
import uuid
from uuid import UUID
from unittest.mock import MagicMock, patch
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.resumes.models import ResumeProfile, ResumeVersion, ResumeTailoringSession, TailoredResumeSuggestion
from app.recommendations.models import RecommendationSignal
from app.events.bus import event_bus

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
        "email": "tailoringuser@example.com",
        "password": "strongpassword123",
        "full_name": "Tailor User",
    }
    await client.post("/api/v1/auth/register", json=register_payload)
    
    login_payload = {
        "email": "tailoringuser@example.com",
        "password": "strongpassword123",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    data = response.json()
    token = data["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def auth_headers_other(client: AsyncClient) -> dict:
    register_payload = {
        "email": "otheruser@example.com",
        "password": "strongpassword123",
        "full_name": "Other User",
    }
    await client.post("/api/v1/auth/register", json=register_payload)
    
    login_payload = {
        "email": "otheruser@example.com",
        "password": "strongpassword123",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    data = response.json()
    token = data["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def uploaded_and_parsed_resume(client: AsyncClient, auth_headers: dict, mock_boto3) -> str:
    # 1. Upload a resume
    files = {"file": ("my_resume.pdf", b"pdf content", "application/pdf")}
    upload_res = await client.post("/api/v1/resumes/upload", files=files, headers=auth_headers)
    assert upload_res.status_code == 201
    version_id = upload_res.json()["id"]

    # 2. Setup mock S3 download
    mock_boto3.get_object.return_value = {
        "Body": MagicMock(read=lambda: b"pdf content")
    }

    # 3. Mock pdfplumber open
    with patch("pdfplumber.open") as mock_pdf_open:
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = (
            "John Doe\njohndoe@example.com\n+123456789\n"
            "Education\nBachelor's in Computer Science\n"
            "Experience\n3 years as a Software Engineer\n"
            "Skills\nPython, FastAPI, Postgres\n"
            "Certifications\nNone"
        )
        mock_pdf.pages = [mock_page]
        mock_pdf_open.return_value.__enter__.return_value = mock_pdf

        # Trigger parse
        parse_res = await client.post(f"/api/v1/resumes/{version_id}/parse", headers=auth_headers)
        assert parse_res.status_code == 200

    return version_id


async def test_tailoring_generation_success(client: AsyncClient, auth_headers: dict, uploaded_and_parsed_resume: str):
    payload = {
        "job_description": "We are looking for a Software Engineer with Python and React skills. AWS Certified is a plus.",
        "job_title": "Software Engineer",
        "company_name": "Innovative Solutions"
    }
    
    resp = await client.post(f"/api/v1/resumes/{uploaded_and_parsed_resume}/tailor", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert "session_id" in data
    assert data["original_ats_score"] > 0
    assert data["tailored_ats_score"] >= data["original_ats_score"]
    assert "improvement_delta" in data
    assert len(data["suggestions"]) > 0
    
    # Check suggestion fields
    suggestion = data["suggestions"][0]
    assert "section_name" in suggestion
    assert "suggestion_type" in suggestion
    assert "suggested_content" in suggestion
    assert "confidence_score" in suggestion
    assert "reason" in suggestion


async def test_tailoring_history(client: AsyncClient, auth_headers: dict, uploaded_and_parsed_resume: str):
    payload = {
        "job_description": "Python, React, AWS required.",
        "job_title": "Fullstack Developer",
        "company_name": "Company A"
    }
    
    # Tailor once
    await client.post(f"/api/v1/resumes/{uploaded_and_parsed_resume}/tailor", json=payload, headers=auth_headers)
    # Tailor twice with different job description to bypass cache
    payload2 = {
        "job_description": "Python, Django, Postgres required.",
        "job_title": "Backend Developer",
        "company_name": "Company B"
    }
    await client.post(f"/api/v1/resumes/{uploaded_and_parsed_resume}/tailor", json=payload2, headers=auth_headers)

    # Fetch history
    history_resp = await client.get(f"/api/v1/resumes/{uploaded_and_parsed_resume}/tailoring-history", headers=auth_headers)
    assert history_resp.status_code == 200
    history_data = history_resp.json()
    assert len(history_data) == 2
    assert history_data[0]["job_title"] == "Fullstack Developer"


async def test_tailoring_session_retrieval(client: AsyncClient, auth_headers: dict, uploaded_and_parsed_resume: str):
    payload = {
        "job_description": "Python, React, AWS required.",
        "job_title": "Fullstack Developer",
        "company_name": "Company A"
    }
    
    tailor_resp = await client.post(f"/api/v1/resumes/{uploaded_and_parsed_resume}/tailor", json=payload, headers=auth_headers)
    session_id = tailor_resp.json()["session_id"]

    # Retrieve session details
    session_resp = await client.get(f"/api/v1/resumes/tailoring/{session_id}", headers=auth_headers)
    assert session_resp.status_code == 200
    session_data = session_resp.json()
    assert session_data["id"] == session_id
    assert session_data["job_title"] == "Fullstack Developer"
    assert len(session_data["suggestions"]) > 0


async def test_tailoring_session_deletion(client: AsyncClient, auth_headers: dict, uploaded_and_parsed_resume: str, db_session: AsyncSession):
    payload = {
        "job_description": "Python and React",
        "job_title": "Backend Dev",
        "company_name": "Tech Corp"
    }
    tailor_resp = await client.post(f"/api/v1/resumes/{uploaded_and_parsed_resume}/tailor", json=payload, headers=auth_headers)
    session_id = tailor_resp.json()["session_id"]

    # Delete session
    del_resp = await client.delete(f"/api/v1/resumes/tailoring/{session_id}", headers=auth_headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "success"

    # Get session details -> should return 404
    get_resp = await client.get(f"/api/v1/resumes/tailoring/{session_id}", headers=auth_headers)
    assert get_resp.status_code == 404

    # Verify suggestions are cascade deleted in DB
    stmt = select(TailoredResumeSuggestion).where(TailoredResumeSuggestion.session_id == UUID(session_id))
    res = await db_session.execute(stmt)
    assert len(list(res.scalars().all())) == 0


async def test_tailoring_ownership_protection(client: AsyncClient, auth_headers: dict, auth_headers_other: dict, uploaded_and_parsed_resume: str):
    payload = {
        "job_description": "Python, Django",
        "job_title": "Django Dev",
        "company_name": "Pythonic Ltd"
    }
    tailor_resp = await client.post(f"/api/v1/resumes/{uploaded_and_parsed_resume}/tailor", json=payload, headers=auth_headers)
    session_id = tailor_resp.json()["session_id"]

    # Try to access with other user's headers
    get_resp = await client.get(f"/api/v1/resumes/tailoring/{session_id}", headers=auth_headers_other)
    assert get_resp.status_code == 404

    # Try to delete with other user's headers
    del_resp = await client.delete(f"/api/v1/resumes/tailoring/{session_id}", headers=auth_headers_other)
    assert del_resp.status_code == 404

    # Try to tailor other user's resume
    tailor_other_resp = await client.post(f"/api/v1/resumes/{uploaded_and_parsed_resume}/tailor", json=payload, headers=auth_headers_other)
    assert tailor_other_resp.status_code == 404


async def test_soft_deleted_resume_protection(client: AsyncClient, auth_headers: dict, uploaded_and_parsed_resume: str, db_session: AsyncSession):
    # Soft delete the profile of this version
    from app.resumes.models import ResumeVersion, ResumeProfile
    stmt_v = select(ResumeVersion).where(ResumeVersion.id == UUID(uploaded_and_parsed_resume))
    version = (await db_session.execute(stmt_v)).scalar_one()
    
    stmt_p = select(ResumeProfile).where(ResumeProfile.id == version.profile_id)
    profile = (await db_session.execute(stmt_p)).scalar_one()
    profile.is_deleted = True
    await db_session.commit()

    payload = {
        "job_description": "Python Dev",
        "job_title": "Developer",
        "company_name": "Acme Inc"
    }

    # Trigger tailoring, should return 404
    resp = await client.post(f"/api/v1/resumes/{uploaded_and_parsed_resume}/tailor", json=payload, headers=auth_headers)
    assert resp.status_code == 404


async def test_deterministic_output(client: AsyncClient, auth_headers: dict, uploaded_and_parsed_resume: str):
    payload = {
        "job_description": "We require Python and React. AWS Certified is required.",
        "job_title": "Full Stack",
        "company_name": "AWS Company"
    }
    resp = await client.post(f"/api/v1/resumes/{uploaded_and_parsed_resume}/tailor?mode=deterministic", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    
    # Check that tailoring history stores the mode
    history_resp = await client.get(f"/api/v1/resumes/{uploaded_and_parsed_resume}/tailoring-history", headers=auth_headers)
    assert history_resp.json()[0]["tailoring_mode"] == "deterministic"


async def test_keyword_detection(client: AsyncClient, auth_headers: dict, uploaded_and_parsed_resume: str):
    # Job description specifies "React" which is missing from uploaded resume
    payload = {
        "job_description": "Must have React.",
        "job_title": "Frontend Engineer",
        "company_name": "Frontend Shop"
    }
    resp = await client.post(f"/api/v1/resumes/{uploaded_and_parsed_resume}/tailor", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    suggestions = resp.json()["suggestions"]
    
    # Check that React is recommended for addition
    keyword_suggestions = [s for s in suggestions if "react" in s["suggested_content"].lower()]
    assert len(keyword_suggestions) > 0
    assert keyword_suggestions[0]["suggestion_type"] in ["keyword_addition", "skill_recommendation"]


async def test_ats_improvement_estimation(client: AsyncClient, auth_headers: dict, uploaded_and_parsed_resume: str):
    payload = {
        "job_description": "Required skills: React, TypeScript, Vue.",
        "job_title": "Lead Engineer",
        "company_name": "MegaCorp"
    }
    resp = await client.post(f"/api/v1/resumes/{uploaded_and_parsed_resume}/tailor", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["tailored_ats_score"] >= data["original_ats_score"]
    assert data["improvement_delta"] == (data["tailored_ats_score"] - data["original_ats_score"])


async def test_explainability_generation(client: AsyncClient, auth_headers: dict, uploaded_and_parsed_resume: str):
    payload = {
        "job_description": "Required: AWS Certified.",
        "job_title": "Cloud Architect",
        "company_name": "Cloud Ltd"
    }
    resp = await client.post(f"/api/v1/resumes/{uploaded_and_parsed_resume}/tailor", json=payload, headers=auth_headers)
    suggestions = resp.json()["suggestions"]
    for s in suggestions:
        assert len(s["reason"]) > 5
        assert "AWS" in s["reason"] or "required" in s["reason"].lower() or "missing" in s["reason"].lower() or "appears" in s["reason"].lower() or "certification" in s["reason"].lower()


async def test_ai_assisted_mode(client: AsyncClient, auth_headers: dict, uploaded_and_parsed_resume: str):
    payload = {
        "job_description": "Python developer wanted.",
        "job_title": "Developer",
        "company_name": "Tech Corp"
    }
    resp = await client.post(f"/api/v1/resumes/{uploaded_and_parsed_resume}/tailor?mode=ai_assisted", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    
    # Verify suggestions returned contain the mock AI content
    suggestions = resp.json()["suggestions"]
    assert any(s["suggestion_type"] == "bullet_rewrite" for s in suggestions)
    
    # Check that tailoring history stores the mode
    history_resp = await client.get(f"/api/v1/resumes/{uploaded_and_parsed_resume}/tailoring-history", headers=auth_headers)
    assert history_resp.json()[0]["tailoring_mode"] == "ai_assisted"


async def test_tailoring_feedback_signal_generation(client: AsyncClient, auth_headers: dict, uploaded_and_parsed_resume: str, db_session: AsyncSession):
    payload = {
        "job_description": "Python, React, AWS.",
        "job_title": "Developer",
        "company_name": "Tech Corp"
    }
    # Reset published events
    event_bus.published_events = []
    
    resp = await client.post(f"/api/v1/resumes/{uploaded_and_parsed_resume}/tailor", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    
    # Verify Recommendation Signals saved in DB
    stmt = select(RecommendationSignal).where(RecommendationSignal.user_id != None)
    res = await db_session.execute(stmt)
    signals = list(res.scalars().all())
    
    signal_types = [sig.signal_type for sig in signals]
    assert "tailoring_completed" in signal_types
    assert any(t in ["tailoring_high_improvement", "tailoring_low_improvement"] for t in signal_types)

    # Verify event published to EventBus
    assert len(event_bus.published_events) > 0
    topic, event = event_bus.published_events[0]
    assert topic == "resume_tailoring_completed"
    assert event.feature_name == "resume_tailoring_completed"
    assert "original_ats_score" in event.interaction_details


async def test_tailoring_cache_reuse(client: AsyncClient, auth_headers: dict, uploaded_and_parsed_resume: str, db_session: AsyncSession):
    payload = {
        "job_description": "We are looking for Python developer.",
        "job_title": "Python Developer",
        "company_name": "Tech Ltd"
    }
    
    # 1. First request -> generates and saves
    resp1 = await client.post(f"/api/v1/resumes/{uploaded_and_parsed_resume}/tailor", json=payload, headers=auth_headers)
    assert resp1.status_code == 201
    session_id1 = resp1.json()["session_id"]
    
    # Count sessions in DB
    stmt = select(ResumeTailoringSession).where(ResumeTailoringSession.resume_version_id == UUID(uploaded_and_parsed_resume))
    res1 = await db_session.execute(stmt)
    sessions1 = list(res1.scalars().all())
    count1 = len(sessions1)
    
    # 2. Second request with exact same details -> should hit cache
    resp2 = await client.post(f"/api/v1/resumes/{uploaded_and_parsed_resume}/tailor", json=payload, headers=auth_headers)
    assert resp2.status_code == 201
    session_id2 = resp2.json()["session_id"]
    
    # Assert session ID is the same (cached reuse)
    assert session_id1 == session_id2
    
    # Count sessions in DB again -> should remain the same
    res2 = await db_session.execute(stmt)
    sessions2 = list(res2.scalars().all())
    assert len(sessions2) == count1


async def test_resume_snapshot_preservation(client: AsyncClient, auth_headers: dict, uploaded_and_parsed_resume: str, db_session: AsyncSession):
    payload = {
        "job_description": "We need Python and Postgres skills.",
        "job_title": "Backend Dev",
        "company_name": "Acme Co"
    }
    resp = await client.post(f"/api/v1/resumes/{uploaded_and_parsed_resume}/tailor", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    session_id = resp.json()["session_id"]
    
    # Fetch session from DB
    stmt = select(ResumeTailoringSession).where(ResumeTailoringSession.id == UUID(session_id))
    session = (await db_session.execute(stmt)).scalar_one()
    
    # Check snapshot is populated and has all required fields
    snapshot = session.resume_snapshot
    assert snapshot is not None
    assert "skills" in snapshot
    assert "education" in snapshot
    assert "experience" in snapshot
    assert "certifications" in snapshot
    assert "summary" in snapshot
    
    # Check content matches uploaded resume data
    assert "Python" in snapshot["skills"]
    assert "Computer Science" in snapshot["education"][0]


async def test_severity_assignment(client: AsyncClient, auth_headers: dict, uploaded_and_parsed_resume: str):
    # Missing skill should trigger skill_recommendation (severity: critical)
    # Missing certification should trigger ats_optimization (severity: high)
    # Keyword addition (severity: low)
    payload = {
        "job_description": "Required skills: React, TypeScript.\nCertification: AWS Certified is a plus.",
        "job_title": "Full Stack Dev",
        "company_name": "Tech Co"
    }
    resp = await client.post(f"/api/v1/resumes/{uploaded_and_parsed_resume}/tailor?mode=deterministic", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    suggestions = resp.json()["suggestions"]
    
    # We should have severity levels assigned
    for s in suggestions:
        assert s["severity_level"] in ["low", "medium", "high", "critical"]
        
    criticals = [s for s in suggestions if s["severity_level"] == "critical"]
    assert len(criticals) > 0  # skill_recommendation
    
    highs = [s for s in suggestions if s["severity_level"] == "high"]
    assert len(highs) > 0  # AWS Certified certification


async def test_tailoring_quality_score(client: AsyncClient, auth_headers: dict, uploaded_and_parsed_resume: str, db_session: AsyncSession):
    payload = {
        "job_description": "Python, React, AWS Certified. Bachelor's required. 5 years experience.",
        "job_title": "Staff Engineer",
        "company_name": "Initech"
    }
    resp = await client.post(f"/api/v1/resumes/{uploaded_and_parsed_resume}/tailor?mode=deterministic", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    session_id = resp.json()["session_id"]
    
    stmt = select(ResumeTailoringSession).where(ResumeTailoringSession.id == UUID(session_id))
    session = (await db_session.execute(stmt)).scalar_one()
    
    # Quality score should be computed and populated
    assert session.tailoring_quality_score is not None
    assert 0 <= session.tailoring_quality_score <= 100


async def test_duplicate_request_idempotency(client: AsyncClient, auth_headers: dict, uploaded_and_parsed_resume: str, db_session: AsyncSession):
    import pytest
    import hashlib
    from sqlalchemy.exc import IntegrityError
    
    # Get user_id from DB
    stmt = select(ResumeTailoringSession).limit(1)
    res = await db_session.execute(stmt)
    first_session = res.scalars().first()
    user_id = first_session.user_id if first_session else UUID(int=1)
    
    dup_session = ResumeTailoringSession(
        user_id=user_id,
        resume_version_id=UUID(uploaded_and_parsed_resume),
        job_description_hash=hashlib.sha256(b"Unique JD content").hexdigest(),
        job_title="Idempotency Tester",
        original_ats_score=50,
        tailored_ats_score=60,
        tailoring_mode="deterministic",
        status="completed"
    )
    
    dup_session2 = ResumeTailoringSession(
        user_id=user_id,
        resume_version_id=UUID(uploaded_and_parsed_resume),
        job_description_hash=hashlib.sha256(b"Unique JD content").hexdigest(),
        job_title="Idempotency Tester",
        original_ats_score=50,
        tailored_ats_score=60,
        tailoring_mode="deterministic",
        status="completed"
    )
    
    db_session.add(dup_session)
    await db_session.commit()
    
    # Try adding again with the same unique key
    db_session.add(dup_session2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


async def test_gemini_timeout_fallback(client: AsyncClient, auth_headers: dict, uploaded_and_parsed_resume: str):
    import asyncio
    payload = {
        "job_description": "We are looking for a Python and React developer.",
        "job_title": "Software Engineer",
        "company_name": "Innovative Solutions"
    }
    
    # Mock GeminiClient.generate_content to raise TimeoutError
    with patch("app.ai.providers.gemini.GeminiClient.generate_content") as mock_generate:
        mock_generate.side_effect = asyncio.TimeoutError()
        
        resp = await client.post(
            f"/api/v1/resumes/{uploaded_and_parsed_resume}/tailor?mode=ai_assisted",
            json=payload,
            headers=auth_headers
        )
        
        # Request should succeed because it falls back to deterministic mode
        assert resp.status_code == 201
        data = resp.json()
        assert "session_id" in data
        assert data["original_ats_score"] > 0
        assert data["tailored_ats_score"] >= data["original_ats_score"]
        # It must have suggestions from deterministic rules
        assert len(data["suggestions"]) > 0


async def test_tailoring_history_soft_deleted_resume(client: AsyncClient, auth_headers: dict, uploaded_and_parsed_resume: str, db_session: AsyncSession):
    payload = {
        "job_description": "Python, Django backend.",
        "job_title": "Backend Developer",
        "company_name": "ACME"
    }
    
    # 1. Create a tailoring session
    tailor_resp = await client.post(
        f"/api/v1/resumes/{uploaded_and_parsed_resume}/tailor",
        json=payload,
        headers=auth_headers
    )
    assert tailor_resp.status_code == 201
    
    # 2. Soft delete the version and profile in the database
    from app.resumes.models import ResumeVersion, ResumeProfile
    stmt_v = select(ResumeVersion).where(ResumeVersion.id == UUID(uploaded_and_parsed_resume))
    version = (await db_session.execute(stmt_v)).scalar_one()
    
    stmt_p = select(ResumeProfile).where(ResumeProfile.id == version.profile_id)
    profile = (await db_session.execute(stmt_p)).scalar_one()
    
    version.is_deleted = True
    profile.is_deleted = True
    await db_session.commit()
    
    # 3. Request history, expected 404
    history_resp = await client.get(
        f"/api/v1/resumes/{uploaded_and_parsed_resume}/tailoring-history",
        headers=auth_headers
    )
    assert history_resp.status_code == 404
    assert history_resp.json()["detail"] == "Resume version not found"


async def test_tailoring_concurrent_duplicate_requests(client: AsyncClient, auth_headers: dict, uploaded_and_parsed_resume: str, db_session: AsyncSession):
    import asyncio
    from app.core.database import get_db
    from tests.conftest import TestingSessionLocal
    from app.main import app

    # Override get_db to return a fresh session per request, simulating production
    async def override_get_db_concurrent():
        async with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db_concurrent

    payload = {
        "job_description": "We need React and AWS Certified expertise.",
        "job_title": "Cloud Dev",
        "company_name": "CloudTech"
    }
    
    try:
        # Fire 10 concurrent requests
        tasks = [
            client.post(
                f"/api/v1/resumes/{uploaded_and_parsed_resume}/tailor?mode=deterministic",
                json=payload,
                headers=auth_headers
            )
            for _ in range(10)
        ]
        
        responses = await asyncio.gather(*tasks)
        
        # Assert all responses are successful (HTTP 201)
        for resp in responses:
            assert resp.status_code == 201
            assert "session_id" in resp.json()
            
        # Assert they all returned the exact same session_id (due to caching and concurrency rollback/cache reuse)
        session_ids = [resp.json()["session_id"] for resp in responses]
        assert len(set(session_ids)) == 1
        
        # Assert exactly 1 session row is created in the database
        from app.resumes.models import ResumeTailoringSession
        stmt = select(ResumeTailoringSession).where(
            ResumeTailoringSession.resume_version_id == UUID(uploaded_and_parsed_resume)
        )
        await db_session.rollback()  # start a new transaction to read committed rows
        res = await db_session.execute(stmt)
        sessions = list(res.scalars().all())
        
        assert len(sessions) == 1
    finally:
        # Restore original get_db override
        async def override_get_db():
            try:
                yield db_session
            finally:
                pass
        app.dependency_overrides[get_db] = override_get_db
        
        # Cleanup database records created by the separate sessions to avoid polluting other tests
        from app.resumes.models import ResumeTailoringSession, TailoredResumeSuggestion, ATSAnalysis
        from sqlalchemy import delete
        
        # Delete tailored suggestions
        await db_session.execute(delete(TailoredResumeSuggestion).where(
            TailoredResumeSuggestion.session_id.in_(
                select(ResumeTailoringSession.id).where(
                    ResumeTailoringSession.resume_version_id == UUID(uploaded_and_parsed_resume)
                )
            )
        ))
        # Delete tailoring sessions
        await db_session.execute(delete(ResumeTailoringSession).where(
            ResumeTailoringSession.resume_version_id == UUID(uploaded_and_parsed_resume)
        ))
        # Delete ATS analyses
        await db_session.execute(delete(ATSAnalysis).where(
            ATSAnalysis.resume_version_id == UUID(uploaded_and_parsed_resume)
        ))
        await db_session.commit()



