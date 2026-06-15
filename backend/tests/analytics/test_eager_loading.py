"""Sprint 10.5 Fix #2 Integration Tests: Eager loading for AnalyticsSnapshot.insights."""
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
        "email": "eager_analytics_user@example.com",
        "password": "strongpassword123",
        "full_name": "Eager Analytics User",
    }
    await client.post("/api/v1/auth/register", json=register_payload)
    login_payload = {
        "email": "eager_analytics_user@example.com",
        "password": "strongpassword123",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    data = response.json()
    return {"Authorization": f"Bearer {data['access_token']}"}


async def test_generate_snapshot_returns_insights(
    client: AsyncClient, auth_headers: dict
):
    """Generating a snapshot should return with insights accessible via eager loading."""
    resp = await client.post("/api/v1/analytics/generate", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "snapshot" in data
    assert "insights" in data
    assert isinstance(data["insights"], list)
    # Should have at least onboarding insights
    assert len(data["insights"]) >= 1


async def test_get_overview_returns_insights(
    client: AsyncClient, auth_headers: dict
):
    """Getting the overview should return insights eagerly loaded without MissingGreenlet."""
    # Generate first
    await client.post("/api/v1/analytics/generate", headers=auth_headers)

    resp = await client.get("/api/v1/analytics", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "snapshot" in data
    assert "insights" in data
    assert isinstance(data["insights"], list)
    assert len(data["insights"]) >= 1


async def test_get_history_returns_snapshots(
    client: AsyncClient, auth_headers: dict
):
    """Getting history should return snapshots without MissingGreenlet."""
    # Generate first
    await client.post("/api/v1/analytics/generate", headers=auth_headers)

    resp = await client.get("/api/v1/analytics/history", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "total_applications" in data[0]


async def test_get_insights_returns_insights(
    client: AsyncClient, auth_headers: dict
):
    """Getting insights should return insights eagerly loaded from the snapshot relationship."""
    # Generate first
    await client.post("/api/v1/analytics/generate", headers=auth_headers)

    resp = await client.get("/api/v1/analytics/insights", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "insight_type" in data[0]
    assert "title" in data[0]
