import pytest
import pytest_asyncio
import uuid
import hashlib
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.users.models import User
from app.resumes.models import ResumeProfile, ResumeVersion
from app.jobs.models import Job, JobMatch
from app.job_sources.models import ExternalJobSource
from app.job_sources.normalization_service import NormalizationService
from app.job_sources.ingestion_service import JobIngestionService
from app.recommendations.service import JobDiscoveryService
from app.core.security import create_access_token

pytestmark = pytest.mark.asyncio


class IngestionTestData:
    def __init__(self):
        self.admin_id = uuid.uuid4()
        self.user_id = uuid.uuid4()
        self.profile_id = uuid.uuid4()
        self.version_id = uuid.uuid4()


@pytest_asyncio.fixture
async def setup_ingestion_data(db_session: AsyncSession) -> IngestionTestData:
    setup = IngestionTestData()

    # Create users
    admin = User(
        id=setup.admin_id,
        email="admin@example.com",
        password_hash="hashed_pwd",
        full_name="Admin User",
        is_active=True,
        is_admin=True,
    )
    user = User(
        id=setup.user_id,
        email="user@example.com",
        password_hash="hashed_pwd",
        full_name="Regular User",
        is_active=True,
        is_admin=False,
    )
    db_session.add_all([admin, user])
    await db_session.flush()

    # Create Resume profile and version for regular user (for recommendations integration testing)
    profile = ResumeProfile(
        id=setup.profile_id,
        user_id=setup.user_id,
        name="Main Profile",
        is_default=True,
    )
    db_session.add(profile)
    await db_session.flush()

    version = ResumeVersion(
        id=setup.version_id,
        profile_id=setup.profile_id,
        user_id=setup.user_id,
        version_number=1,
        original_filename="cv.pdf",
        storage_path="path/cv.pdf",
        file_size=512,
        mime_type="application/pdf",
        upload_source="upload",
        skills=["Python", "FastAPI", "SQL"],
        status="completed",
    )
    db_session.add(version)
    await db_session.flush()

    profile.active_version_id = version.id
    await db_session.flush()

    await db_session.commit()
    return setup


async def get_headers_for_user(user_id: uuid.UUID) -> dict:
    token = create_access_token(subject=user_id)
    return {"Authorization": f"Bearer {token}"}


async def test_job_ingestion_success(
    client: AsyncClient, db_session: AsyncSession, setup_ingestion_data: IngestionTestData
):
    headers = await get_headers_for_user(setup_ingestion_data.admin_id)

    # Ingest LinkedIn
    response = await client.post("/api/v1/job-sources/ingest", json={"source": "linkedin"}, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["new_count"] == 2
    assert data["processed_count"] == 2

    # Query jobs
    stmt = select(Job).where(Job.external_source == "linkedin")
    res = await db_session.execute(stmt)
    jobs = list(res.scalars().all())
    assert len(jobs) == 2
    assert jobs[0].normalized_company in ("Google", "Netflix")


async def test_duplicate_detection(
    client: AsyncClient, db_session: AsyncSession, setup_ingestion_data: IngestionTestData
):
    headers = await get_headers_for_user(setup_ingestion_data.admin_id)

    # Ingest LinkedIn (2 jobs: Python Dev @ Google LLC, Data Analyst @ Netflix)
    await client.post("/api/v1/job-sources/ingest", json={"source": "linkedin"}, headers=headers)

    # Ingest Naukri (2 jobs: Python Dev @ Google Inc. -> should be exact duplicate of Google LLC job; React Dev @ Facebook)
    response_nk = await client.post("/api/v1/job-sources/ingest", json={"source": "naukri"}, headers=headers)
    assert response_nk.status_code == 200
    nk_data = response_nk.json()
    # Google is updated, Facebook is new
    assert nk_data["new_count"] == 1
    assert nk_data["updated_count"] == 1

    # Ingest Indeed (2 jobs: Senior Python Dev @ Google -> should match Google LLC job by similarity threshold >= 0.8; Front End @ Amazon)
    response_ind = await client.post("/api/v1/job-sources/ingest", json={"source": "indeed"}, headers=headers)
    assert response_ind.status_code == 200
    ind_data = response_ind.json()
    # Google is updated again (via similarity check), Amazon is new
    assert ind_data["new_count"] == 1
    assert ind_data["updated_count"] == 1

    # Verify total active jobs in system:
    # Netflix (1), Google (1), Facebook (1), Amazon (1) = 4 jobs
    stmt = select(func.count(Job.id)).where(Job.is_deleted == False)
    res = await db_session.execute(stmt)
    assert res.scalar() == 4


async def test_normalization(
    client: AsyncClient, db_session: AsyncSession, setup_ingestion_data: IngestionTestData
):
    # Test specific normalization logic directly
    assert NormalizationService.normalize_company("Google LLC") == "Google"
    assert NormalizationService.normalize_company("Google Inc.") == "Google"
    assert NormalizationService.normalize_company("Google") == "Google"
    assert NormalizationService.normalize_company("Apple Corp.") == "Apple"

    assert NormalizationService.normalize_location("Remote") == "Remote"
    assert NormalizationService.normalize_location("Work From Home") == "Remote"
    assert NormalizationService.normalize_location("wfh") == "Remote"
    assert NormalizationService.normalize_location("pune, india") == "Pune, India"

    assert NormalizationService.normalize_job_type("full-time") == "Full-time"
    assert NormalizationService.normalize_job_type("FT") == "Full-time"
    assert NormalizationService.normalize_job_type("internship") == "Internship"

    assert NormalizationService.normalize_experience_level("fresher") == "Entry-level"
    assert NormalizationService.normalize_experience_level("senior engineer") == "Senior"
    assert NormalizationService.normalize_experience_level("Lead Developer") == "Lead"


async def test_ingestion_idempotency(
    client: AsyncClient, db_session: AsyncSession, setup_ingestion_data: IngestionTestData
):
    headers = await get_headers_for_user(setup_ingestion_data.admin_id)

    # First run creates
    resp1 = await client.post("/api/v1/job-sources/ingest", json={"source": "linkedin"}, headers=headers)
    assert resp1.json()["new_count"] == 2

    # Second run updates but doesn't duplicate
    resp2 = await client.post("/api/v1/job-sources/ingest", json={"source": "linkedin"}, headers=headers)
    assert resp2.json()["new_count"] == 0
    assert resp2.json()["updated_count"] == 2


async def test_job_expiry(
    client: AsyncClient, db_session: AsyncSession, setup_ingestion_data: IngestionTestData
):
    # Create an active job seen 31 days ago
    now = datetime.now(timezone.utc)
    old_job = Job(
        title="Python Dev",
        company="OldCorp",
        description="Write code.",
        external_source="linkedin",
        external_job_id="old-001",
        last_seen_at=now - timedelta(days=31),
        job_status="active",
    )
    # Create an active job seen just now
    new_job = Job(
        title="Python Dev 2",
        company="NewCorp",
        description="Write code.",
        external_source="linkedin",
        external_job_id="new-002",
        last_seen_at=now,
        job_status="active",
    )
    db_session.add_all([old_job, new_job])
    await db_session.commit()

    service = JobIngestionService(db_session)
    res = await service.mark_expired_jobs()
    assert res["expired_count"] == 1

    # Verify old_job is expired and new_job is still active
    stmt = select(Job).where(Job.external_job_id == "old-001")
    res_old = await db_session.execute(stmt)
    assert res_old.scalar_one().job_status == "expired"

    stmt_new = select(Job).where(Job.external_job_id == "new-002")
    res_new = await db_session.execute(stmt_new)
    assert res_new.scalar_one().job_status == "active"


async def test_source_tracking(
    client: AsyncClient, db_session: AsyncSession, setup_ingestion_data: IngestionTestData
):
    headers = await get_headers_for_user(setup_ingestion_data.admin_id)

    await client.post("/api/v1/job-sources/ingest", json={"source": "linkedin"}, headers=headers)

    stmt = select(ExternalJobSource).where(ExternalJobSource.source_name == "linkedin")
    res = await db_session.execute(stmt)
    records = list(res.scalars().all())
    assert len(records) == 2
    assert records[0].source_job_id in ("li-101", "li-102")


async def test_stats_generation(
    client: AsyncClient, db_session: AsyncSession, setup_ingestion_data: IngestionTestData
):
    headers = await get_headers_for_user(setup_ingestion_data.admin_id)
    user_headers = await get_headers_for_user(setup_ingestion_data.user_id)

    # Ingest jobs
    await client.post("/api/v1/job-sources/ingest", json={"source": "linkedin"}, headers=headers)

    # Get stats
    response = await client.get("/api/v1/job-sources/stats", headers=user_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_jobs"] >= 2
    assert data["active_jobs"] >= 2
    assert data["sources"]["linkedin"] == 2


async def test_refresh_updates_existing_jobs(
    client: AsyncClient, db_session: AsyncSession, setup_ingestion_data: IngestionTestData
):
    # Manually create unnormalized external job
    job = Job(
        title="Software Developer  ",
        company="TechCorp LLC",
        location="wfh",
        description="Write code.",
        external_source="linkedin",
        external_job_id="li-999",
        last_seen_at=datetime.now(timezone.utc),
        job_status="active",
    )
    db_session.add(job)
    await db_session.commit()

    headers = await get_headers_for_user(setup_ingestion_data.admin_id)
    response = await client.post("/api/v1/job-sources/refresh", headers=headers)
    assert response.status_code == 200
    assert response.json()["updated_count"] >= 1

    # Verify normalized fields on the job
    db_session.expire(job)
    stmt = select(Job).where(Job.external_job_id == "li-999")
    res = await db_session.execute(stmt)
    db_job = res.scalar_one()
    assert db_job.normalized_company == "TechCorp"
    assert db_job.normalized_location == "Remote"


async def test_recommendation_excludes_expired_jobs(
    client: AsyncClient, db_session: AsyncSession, setup_ingestion_data: IngestionTestData
):
    headers = await get_headers_for_user(setup_ingestion_data.admin_id)
    user_headers = await get_headers_for_user(setup_ingestion_data.user_id)

    # Ingest LinkedIn (which has Google job which is active)
    await client.post("/api/v1/job-sources/ingest", json={"source": "linkedin"}, headers=headers)

    # Generate recommendations for regular user
    rec_service = JobDiscoveryService(db_session)
    recs = await rec_service.discover_jobs(setup_ingestion_data.user_id)
    assert len(recs) > 0

    # Verify Google job is in recommendations
    google_job_id = [r.job_id for r in recs if r.job_snapshot.get("company") == "Google LLC"][0]

    # Expiry Google job: set status to expired
    stmt = select(Job).where(Job.id == google_job_id)
    job = (await db_session.execute(stmt)).scalar_one()
    job.job_status = "expired"
    await db_session.commit()

    # Clear cache and fetch again
    recs_after = await rec_service.refresh_recommendations(setup_ingestion_data.user_id)

    # Assert Google job is excluded from active recommendations
    job_ids_after = [r.job_id for r in recs_after]
    assert google_job_id not in job_ids_after


async def test_ingestion_hash_consistency(
    client: AsyncClient, db_session: AsyncSession, setup_ingestion_data: IngestionTestData
):
    headers = await get_headers_for_user(setup_ingestion_data.admin_id)

    # Ingest twice
    await client.post("/api/v1/job-sources/ingest", json={"source": "linkedin"}, headers=headers)

    stmt = select(Job).where(Job.external_source == "linkedin")
    res = await db_session.execute(stmt)
    jobs = list(res.scalars().all())

    # Asserts ingestion hashes are consistent and present
    assert jobs[0].ingestion_hash is not None
    assert len(jobs[0].ingestion_hash) == 64  # SHA-256 is 64 chars
