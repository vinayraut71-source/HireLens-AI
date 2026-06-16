import pytest
import pytest_asyncio
import uuid
import asyncio
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.users.models import User
from app.job_sources.models import ProviderSyncLog
from app.job_sources.providers.base import BaseJobProvider
from app.job_sources.provider_registry import ProviderRegistry
from app.job_sources.rate_limiter import ProviderRateLimiter
from app.job_sources.provider_health import ProviderHealthService
from app.job_sources.sync_audit import SyncAudit
from app.job_sources.sync_scheduler import SyncScheduler
from app.core.security import create_access_token

pytestmark = pytest.mark.asyncio


class DummyFailingProvider(BaseJobProvider):
    async def fetch_jobs(self) -> list[dict]:
        raise ValueError("Simulated network outage")


class DummySuccessProvider(BaseJobProvider):
    async def fetch_jobs(self) -> list[dict]:
        return [
            {
                "external_job_id": "dum-99",
                "title": "Staff Engineer",
                "company": "Dummy Corp",
                "description": "Maintain mock systems.",
                "location": "Remote",
                "source_url": "https://dummy.com/jobs/99"
            }
        ]


class FrameworkTestData:
    def __init__(self):
        self.admin_id = uuid.uuid4()
        self.user_id = uuid.uuid4()


@pytest_asyncio.fixture
async def setup_framework_data(db_session: AsyncSession) -> FrameworkTestData:
    setup = FrameworkTestData()
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
    await db_session.commit()
    return setup


async def get_headers_for_user(user_id: uuid.UUID) -> dict:
    token = create_access_token(subject=user_id)
    return {"Authorization": f"Bearer {token}"}


async def test_provider_registration():
    # Register dummy provider
    dummy = DummySuccessProvider()
    ProviderRegistry.register_provider("dummy_success", dummy)
    assert ProviderRegistry.is_enabled("dummy_success") is True
    providers = ProviderRegistry.list_providers()
    assert any(p["name"] == "dummy_success" for p in providers)


async def test_provider_enable_disable(client: AsyncClient, setup_framework_data: FrameworkTestData):
    headers = await get_headers_for_user(setup_framework_data.admin_id)

    # Disable linkedin
    ProviderRegistry.disable_provider("linkedin")
    assert ProviderRegistry.is_enabled("linkedin") is False

    # Toggle via API -> should enable it
    resp = await client.patch("/api/v1/job-sources/providers/linkedin/toggle", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["enabled"] is True
    assert ProviderRegistry.is_enabled("linkedin") is True

    # Toggle again -> should disable it
    resp2 = await client.patch("/api/v1/job-sources/providers/linkedin/toggle", headers=headers)
    assert resp2.status_code == 200
    assert resp2.json()["enabled"] is False
    assert ProviderRegistry.is_enabled("linkedin") is False

    # Restore default
    ProviderRegistry.enable_provider("linkedin")


async def test_scheduler_execution(
    client: AsyncClient, db_session: AsyncSession, setup_framework_data: FrameworkTestData
):
    headers = await get_headers_for_user(setup_framework_data.admin_id)
    # Register a unique success provider for execution testing
    ProviderRegistry.register_provider("dummy_exec", DummySuccessProvider())

    # Trigger sync
    response = await client.post("/api/v1/job-sources/sync/dummy_exec", headers=headers)
    assert response.status_code == 200
    assert response.json()["processed_count"] == 1
    assert response.json()["new_count"] == 1

    # Check sync audit log
    stmt = select(ProviderSyncLog).where(ProviderSyncLog.provider_name == "dummy_exec")
    res = await db_session.execute(stmt)
    logs = list(res.scalars().all())
    assert len(logs) == 1
    assert logs[0].status == "success"
    assert logs[0].jobs_received == 1


async def test_rate_limit_enforcement(
    client: AsyncClient, setup_framework_data: FrameworkTestData
):
    headers = await get_headers_for_user(setup_framework_data.admin_id)
    # Register provider for rate limit check
    ProviderRegistry.register_provider("dummy_ratelimit", DummySuccessProvider())
    
    # Configure min interval
    ProviderRateLimiter._min_intervals["dummy_ratelimit"] = 5.0
    ProviderRateLimiter.record_success("dummy_ratelimit")

    # Call sync -> should fail with 429 because interval is 5.0 and last call was just now
    resp = await client.post("/api/v1/job-sources/sync/dummy_ratelimit", headers=headers)
    assert resp.status_code == 429
    assert "Retry after" in resp.json()["detail"]
    assert "Retry-After" in resp.headers


async def test_retry_logic(
    db_session: AsyncSession, setup_framework_data: FrameworkTestData
):
    ProviderRegistry.register_provider("dummy_failing_retry", DummyFailingProvider())
    scheduler = SyncScheduler(db_session)

    # Enforce fast interval for retry wait (0.1 seconds)
    ProviderRateLimiter._min_intervals["dummy_failing_retry"] = 0.1

    # Execute sync with max_retries = 2. It should attempt 3 times (1 initial + 2 retries) and then raise 502
    with pytest.raises(Exception) as exc_info:
        await scheduler.sync_provider("dummy_failing_retry", max_retries=2)
    
    # Check that 3 failed sync logs were created
    stmt = select(ProviderSyncLog).where(ProviderSyncLog.provider_name == "dummy_failing_retry")
    res = await db_session.execute(stmt)
    logs = sorted(list(res.scalars().all()), key=lambda l: l.sync_started_at)
    assert len(logs) == 3
    assert logs[0].status == "retrying"
    assert logs[1].status == "retrying"
    assert logs[2].status == "failed"
    for log in logs:
        assert "Simulated network outage" in log.error_message


async def test_provider_health_updates(
    db_session: AsyncSession, setup_framework_data: FrameworkTestData
):
    # Register and mock 3 consecutive failures to trigger unavailable state
    ProviderRegistry.register_provider("dummy_unhealthy", DummyFailingProvider())
    scheduler = SyncScheduler(db_session)
    ProviderRateLimiter._min_intervals["dummy_unhealthy"] = 0.05

    # Run and fail 3 times
    for _ in range(3):
        # Reset rate limiter to bypass cooldown check
        state = ProviderRateLimiter._get_state("dummy_unhealthy")
        state["last_call_time"] = 0.0
        state["attempts"] = 0
        state["cooldown_until"] = 0.0
        try:
            await scheduler.sync_provider("dummy_unhealthy", max_retries=0)
        except Exception:
            pass

    # Health status should now be unavailable
    health = await ProviderHealthService.get_health(db_session, "dummy_unhealthy")
    assert health["status"] == "unavailable"
    assert health["success_rate"] == 0.0


async def test_sync_logging(
    db_session: AsyncSession, setup_framework_data: FrameworkTestData
):
    # Verify SyncAudit logger utility directly
    log = await SyncAudit.create_log(db_session, "audit_test")
    assert log.status == "running"
    
    completed = await SyncAudit.complete_log(
        db=db_session,
        log_id=log.id,
        jobs_received=10,
        jobs_created=8,
        jobs_updated=2,
        jobs_expired=1,
        status="success"
    )
    assert completed.status == "success"
    assert completed.jobs_created == 8
    assert completed.sync_completed_at is not None


async def test_sync_failure_handling(
    client: AsyncClient, db_session: AsyncSession, setup_framework_data: FrameworkTestData
):
    headers = await get_headers_for_user(setup_framework_data.admin_id)
    ProviderRegistry.register_provider("dummy_fail_direct", DummyFailingProvider())
    ProviderRateLimiter._min_intervals["dummy_fail_direct"] = 0.1

    # Call sync via API -> should return 502 Bad Gateway
    response = await client.post("/api/v1/job-sources/sync/dummy_fail_direct", headers=headers)
    assert response.status_code == 502
    assert "Simulated network outage" in response.json()["detail"]


async def test_provider_discovery(client: AsyncClient, setup_framework_data: FrameworkTestData):
    headers = await get_headers_for_user(setup_framework_data.admin_id)

    # Authenticated list registered providers
    response = await client.get("/api/v1/job-sources/providers", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert any(p["name"] == "linkedin" for p in data)


async def test_audit_log_generation(
    client: AsyncClient, db_session: AsyncSession, setup_framework_data: FrameworkTestData
):
    headers = await get_headers_for_user(setup_framework_data.admin_id)
    
    # Generate some logs
    await SyncAudit.create_log(db_session, "audit_log_history_test")
    await db_session.commit()

    # Call sync history endpoint
    resp = await client.get("/api/v1/job-sources/sync-history", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["provider_name"] == "audit_log_history_test"


async def test_provider_locking(db_session: AsyncSession, setup_framework_data: FrameworkTestData):
    ProviderRegistry.register_provider("dummy_locked", DummySuccessProvider())
    scheduler = SyncScheduler(db_session)
    
    # Acquire lock manually
    from app.job_sources.models import ProviderLock
    from datetime import datetime, timezone, timedelta
    lock = ProviderLock(
        provider_name="dummy_locked",
        locked_until=datetime.now(timezone.utc) + timedelta(seconds=10),
        locked_by="other-process"
    )
    db_session.add(lock)
    await db_session.commit()
    
    # Try running sync -> should skip and return locked status
    res = await scheduler.sync_provider("dummy_locked")
    assert res["status"] == "locked"
    assert res["processed_count"] == 0


async def test_dead_letter_queue(db_session: AsyncSession, setup_framework_data: FrameworkTestData):
    ProviderRegistry.register_provider("dummy_dlq", DummyFailingProvider())
    scheduler = SyncScheduler(db_session)
    
    # Reset rate limiter
    state = ProviderRateLimiter._get_state("dummy_dlq")
    state["last_call_time"] = 0.0
    state["attempts"] = 0
    state["cooldown_until"] = 0.0
    ProviderRateLimiter._min_intervals["dummy_dlq"] = 0.01

    from fastapi import HTTPException
    with pytest.raises(HTTPException):
        await scheduler.sync_provider("dummy_dlq", max_retries=1)

    # Check failed_sync_jobs table
    from app.job_sources.models import FailedSyncJob
    from sqlalchemy import select
    stmt = select(FailedSyncJob).where(FailedSyncJob.provider_name == "dummy_dlq")
    res = await db_session.execute(stmt)
    jobs = list(res.scalars().all())
    assert len(jobs) == 1
    assert jobs[0].provider_name == "dummy_dlq"
    assert "Simulated network outage" in jobs[0].error_message
    assert jobs[0].retry_count == 2


async def test_provider_config_override(client: AsyncClient, db_session: AsyncSession, setup_framework_data: FrameworkTestData):
    headers = await get_headers_for_user(setup_framework_data.admin_id)
    ProviderRegistry.register_provider("dummy_override", DummySuccessProvider())
    
    # Update config via override API
    payload = {
        "sync_interval_minutes": 15,
        "rate_limit_per_hour": 15,
        "retry_limit": 5,
        "timeout_seconds": 45
    }
    resp = await client.patch("/api/v1/job-sources/providers/dummy_override/config", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["sync_interval_minutes"] == 15
    assert data["rate_limit_per_hour"] == 15
    assert data["retry_limit"] == 5
    assert data["timeout_seconds"] == 45

    # Verify loaded config inside database
    from app.job_sources.models import ProviderConfig
    config = await ProviderConfig.get_or_create(db_session, "dummy_override")
    assert config.retry_limit == 5
    assert config.timeout_seconds == 45


async def test_sync_duration_tracking(db_session: AsyncSession, setup_framework_data: FrameworkTestData):
    ProviderRegistry.register_provider("dummy_duration", DummySuccessProvider())
    scheduler = SyncScheduler(db_session)
    
    # Clear rate limiter
    state = ProviderRateLimiter._get_state("dummy_duration")
    state["last_call_time"] = 0.0
    state["attempts"] = 0
    state["cooldown_until"] = 0.0
    ProviderRateLimiter._min_intervals["dummy_duration"] = 0.01

    await scheduler.sync_provider("dummy_duration")
    
    from app.job_sources.models import ProviderSyncLog
    from sqlalchemy import select
    stmt = select(ProviderSyncLog).where(ProviderSyncLog.provider_name == "dummy_duration")
    res = await db_session.execute(stmt)
    logs = list(res.scalars().all())
    assert len(logs) == 1
    assert logs[0].execution_duration_ms >= 0
    assert logs[0].records_processed == 1


async def test_disabled_provider_health(db_session: AsyncSession, setup_framework_data: FrameworkTestData):
    ProviderRegistry.register_provider("dummy_disabled_health", DummySuccessProvider())
    from app.job_sources.models import ProviderConfig
    config = await ProviderConfig.get_or_create(db_session, "dummy_disabled_health")
    config.enabled = False
    await db_session.commit()
    
    health = await ProviderHealthService.get_health(db_session, "dummy_disabled_health")
    assert health["status"] == "disabled"


async def test_pagination_sync_history(client: AsyncClient, db_session: AsyncSession, setup_framework_data: FrameworkTestData):
    headers = await get_headers_for_user(setup_framework_data.admin_id)
    
    # Create multiple history logs
    for i in range(5):
        await SyncAudit.create_log(db_session, f"pag_test_{i}")
    await db_session.commit()
    
    # Request page=1, page_size=2
    resp = await client.get("/api/v1/job-sources/sync-history?page=1&page_size=2", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    
    # Request page=2, page_size=2
    resp2 = await client.get("/api/v1/job-sources/sync-history?page=2&page_size=2", headers=headers)
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert len(data2) == 2
    assert data2[0]["provider_name"] != data[0]["provider_name"]

    # Test page_size validation
    resp3 = await client.get("/api/v1/job-sources/sync-history?page_size=101", headers=headers)
    assert resp3.status_code == 400
    assert "page_size cannot exceed 100" in resp3.json()["detail"]


async def test_provider_toggle_audit(client: AsyncClient, db_session: AsyncSession, setup_framework_data: FrameworkTestData):
    headers = await get_headers_for_user(setup_framework_data.admin_id)
    ProviderRegistry.register_provider("dummy_audit_toggle", DummySuccessProvider())
    
    # Toggle via API
    resp = await client.patch("/api/v1/job-sources/providers/dummy_audit_toggle/toggle", headers=headers)
    assert resp.status_code == 200
    
    # Verify audit log in db
    from app.job_sources.models import ProviderToggleAudit
    from sqlalchemy import select
    stmt = select(ProviderToggleAudit).where(ProviderToggleAudit.provider_name == "dummy_audit_toggle")
    res = await db_session.execute(stmt)
    audits = list(res.scalars().all())
    assert len(audits) == 1
    assert audits[0].admin_user_id == setup_framework_data.admin_id
    assert audits[0].old_state is True
    assert audits[0].new_state is False


async def test_provider_registration_lifecycle():
    prov = DummySuccessProvider()
    ProviderRegistry.register_provider("lifecycle_temp", prov)
    assert ProviderRegistry.get_provider("lifecycle_temp") is prov
    
    ProviderRegistry.unregister_provider("lifecycle_temp")
    assert ProviderRegistry.get_provider("lifecycle_temp") is None
    assert ProviderRegistry.is_enabled("lifecycle_temp") is False


async def test_rate_limiter_cooldown(db_session: AsyncSession):
    import time
    # Reset state
    state = ProviderRateLimiter._get_state("dummy_cooldown_check")
    state["last_call_time"] = 0.0
    state["attempts"] = 0
    state["cooldown_until"] = time.time() + 10.0
    
    # Should be rate limited
    assert await ProviderRateLimiter.check_rate_limit("dummy_cooldown_check", db_session) is False
    assert await ProviderRateLimiter.get_retry_after("dummy_cooldown_check", db_session) > 0.0


async def test_failed_jobs_retries_non_exhausted(db_session: AsyncSession, setup_framework_data: FrameworkTestData):
    from app.job_sources.models import FailedSyncJob
    from sqlalchemy import select
    stmt = select(FailedSyncJob).where(FailedSyncJob.provider_name == "dummy_non_exhausted")
    res = await db_session.execute(stmt)
    assert len(list(res.scalars().all())) == 0


async def test_stale_lock_cleanup(db_session: AsyncSession):
    from app.job_sources.models import ProviderLock
    from app.job_sources.sync_scheduler import ProviderLockService
    from datetime import datetime, timezone, timedelta
    
    provider_name = "dummy_stale_lock"
    now = datetime.now(timezone.utc)
    
    # 1. Create a stale lock (locked_until in the past)
    stale_lock = ProviderLock(
        provider_name=provider_name,
        locked_until=now - timedelta(seconds=10),
        locked_by="old-worker",
        created_at=now - timedelta(seconds=20)
    )
    db_session.add(stale_lock)
    await db_session.commit()
    
    # 2. Acquire lock -> should succeed because the lock is stale
    acquired = await ProviderLockService.acquire_lock(
        db=db_session,
        provider_name=provider_name,
        timeout_seconds=30,
        worker_id="new-worker"
    )
    assert acquired is True
    
    # Check the lock in db
    stmt = select(ProviderLock).where(ProviderLock.provider_name == provider_name)
    res = await db_session.execute(stmt)
    lock = res.scalar_one()
    assert lock.locked_by == "new-worker"
    
    locked_until_naive = lock.locked_until.replace(tzinfo=None) if lock.locked_until.tzinfo else lock.locked_until
    now_naive = now.replace(tzinfo=None) if now.tzinfo else now
    assert locked_until_naive > now_naive


async def test_health_warning_state(db_session: AsyncSession):
    # Register dummy provider
    ProviderRegistry.register_provider("dummy_warning_health", DummySuccessProvider())
    
    # Create 9 success logs and 1 failure log (total 10 runs -> 10% failure rate)
    from app.job_sources.models import ProviderSyncLog
    from datetime import datetime, timezone, timedelta
    
    now = datetime.now(timezone.utc)
    # Add 9 successes
    for i in range(9):
        log = ProviderSyncLog(
            provider_name="dummy_warning_health",
            sync_started_at=now - timedelta(minutes=i*10),
            sync_completed_at=now - timedelta(minutes=i*10) + timedelta(seconds=5),
            status="success",
            jobs_received=1,
            jobs_created=1,
            records_processed=1,
            execution_duration_ms=5000,
        )
        db_session.add(log)
    
    # Add 1 failure
    fail_log = ProviderSyncLog(
        provider_name="dummy_warning_health",
        sync_started_at=now - timedelta(minutes=95),
        sync_completed_at=now - timedelta(minutes=95) + timedelta(seconds=2),
        status="failed",
        error_message="Oops",
        records_processed=0,
        execution_duration_ms=2000,
    )
    db_session.add(fail_log)
    await db_session.commit()
    
    health = await ProviderHealthService.get_health(db_session, "dummy_warning_health")
    assert health["status"] == "warning"
    assert health["success_rate"] == 0.9  # 9/10 = 90%


async def test_dlq_replay(client: AsyncClient, db_session: AsyncSession, setup_framework_data: FrameworkTestData):
    headers = await get_headers_for_user(setup_framework_data.admin_id)
    
    # Register success provider
    ProviderRegistry.register_provider("dummy_dlq_replay", DummySuccessProvider())
    
    # Create FailedSyncJob in db
    from app.job_sources.models import FailedSyncJob
    job = FailedSyncJob(
        provider_name="dummy_dlq_replay",
        payload={"dummy": "data"},
        error_message="Initial failure",
        retry_count=3,
        resolved=False
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)
    
    # POST replay via API
    resp = await client.post(f"/api/v1/job-sources/failed-syncs/{job.id}/replay", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"
    
    # Verify job is resolved in db
    stmt = select(FailedSyncJob).where(FailedSyncJob.id == job.id)
    res = await db_session.execute(stmt)
    updated_job = res.scalar_one()
    assert updated_job.resolved is True
    assert updated_job.resolved_at is not None


async def test_disabled_provider_sync_rejected(client: AsyncClient, db_session: AsyncSession, setup_framework_data: FrameworkTestData):
    headers = await get_headers_for_user(setup_framework_data.admin_id)
    ProviderRegistry.register_provider("dummy_disabled_sync", DummySuccessProvider())
    
    # Disable via config
    from app.job_sources.models import ProviderConfig
    config = await ProviderConfig.get_or_create(db_session, "dummy_disabled_sync")
    config.enabled = False
    await db_session.commit()
    
    # Trigger sync via API -> should return 400 Bad Request
    resp = await client.post("/api/v1/job-sources/sync/dummy_disabled_sync", headers=headers)
    assert resp.status_code == 400
    assert "disabled" in resp.json()["detail"]


async def test_provider_toggle_audit_reason(client: AsyncClient, db_session: AsyncSession, setup_framework_data: FrameworkTestData):
    headers = await get_headers_for_user(setup_framework_data.admin_id)
    ProviderRegistry.register_provider("dummy_toggle_reason", DummySuccessProvider())
    
    # Toggle with reason
    reason = "Maintenance window scheduled"
    resp = await client.patch(
        f"/api/v1/job-sources/providers/dummy_toggle_reason/toggle?reason={reason}", 
        headers=headers
    )
    assert resp.status_code == 200
    
    # Check Toggle Audit in db
    from app.job_sources.models import ProviderToggleAudit
    stmt = select(ProviderToggleAudit).where(ProviderToggleAudit.provider_name == "dummy_toggle_reason")
    res = await db_session.execute(stmt)
    audits = list(res.scalars().all())
    assert len(audits) == 1
    assert audits[0].reason == reason

