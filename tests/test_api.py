import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/health")
        assert resp.status_code == 200
        assert resp.json().get("ok") is True

@pytest.mark.asyncio
async def test_me_unauth():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/me")
        assert resp.status_code == 403

@pytest.mark.asyncio
async def test_clients_list_unauth():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/clients")
        assert resp.status_code == 403

@pytest.mark.asyncio
async def test_jobs_list_unauth():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/jobs")
        assert resp.status_code == 403
