import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_species_returns_200(client: AsyncClient):
    response = await client.get("/v1/species/")
    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert "total" in body
    assert "limit" in body
    assert "offset" in body


@pytest.mark.asyncio
async def test_search_species_returns_200(client: AsyncClient):
    response = await client.get("/v1/species/search", params={"q": "ca"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_create_species_returns_201(client: AsyncClient):
    payload = {
        "scientific_name": "Testus speciesus",
        "common_name": "Test Species",
        "kingdom": "Animalia",
    }
    response = await client.post("/v1/species/", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["scientific_name"] == "Testus speciesus"
    assert "id" in body
