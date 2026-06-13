import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_auth_flow(client: AsyncClient):
    # 1. Register a new user
    register_payload = {
        "email": "testuser@example.com",
        "password": "strongpassword123",
        "full_name": "Test User",
    }
    response = await client.post("/api/v1/auth/register", json=register_payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["email"] == "testuser@example.com"
    assert data["full_name"] == "Test User"
    assert "access_token" in data
    assert "refresh_token" in data

    # 2. Register duplicate user - Conflict
    response = await client.post("/api/v1/auth/register", json=register_payload)
    assert response.status_code == 409
    assert response.json()["detail"] == "Email already registered"

    # 3. Login with correct credentials (testing email normalization)
    login_payload = {
        "email": "  TESTUSER@example.com  ",
        "password": "strongpassword123",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    login_data = response.json()
    assert "access_token" in login_data
    assert "refresh_token" in login_data
    assert login_data["token_type"] == "bearer"

    # 4. Login with incorrect password
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "testuser@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401

    # 5. Fetch current user profile (/me)
    access_token = login_data["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    me_data = response.json()
    assert me_data["email"] == "testuser@example.com"
    assert me_data["full_name"] == "Test User"

    # 6. Fetch /me without credentials - Unauthorized
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401

    # 7. Refresh access token using rotation
    refresh_token = login_data["refresh_token"]
    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert response.status_code == 200
    refresh_data = response.json()
    assert "access_token" in refresh_data
    assert "refresh_token" in refresh_data
    assert refresh_data["refresh_token"] != refresh_token  # Rotated on use

    # 8. Try to use old refresh token again - Unauthorized (since rotated/revoked)
    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert response.status_code == 401

    # 9. Logout
    new_refresh_token = refresh_data["refresh_token"]
    response = await client.post(
        "/api/v1/auth/logout", json={"refresh_token": new_refresh_token}
    )
    assert response.status_code == 204

    # 10. Verify refresh token is revoked after logout
    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": new_refresh_token}
    )
    assert response.status_code == 401
