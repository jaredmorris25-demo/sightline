import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_get_sightings_no_auth_returns_200(client):
    """GET /v1/sightings is a public endpoint — no Authorization header required."""
    response = await client.get("/v1/sightings/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_post_sighting_no_auth_returns_401():
    """POST /v1/sightings is a protected endpoint — missing token returns 401."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/v1/sightings/", json={})
    assert response.status_code == 401
