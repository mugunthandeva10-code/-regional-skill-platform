import pytest
from app.models import User


class TestApiSmoke:
    async def test_health(self, client):
        r = await client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    async def test_register_then_profile_not_found(self, client):
        r = await client.post("/auth/register", json={
            "full_name": "New Student", "email": "new@demo.local", "password": "demo1234",
            "location": "Chennai",
        })
        assert r.status_code == 201
        token = r.json()["access_token"]
        r2 = await client.get("/students/profile", headers={"Authorization": f"Bearer {token}"})
        assert r2.status_code == 404

    async def test_admin_only_route_requires_admin(self, client):
        # register a student
        r = await client.post("/auth/register", json={
            "full_name": "Student", "email": "stu@demo.local", "password": "demo1234"
        })
        token = r.json()["access_token"]
        r2 = await client.get("/admin/statistics", headers={"Authorization": f"Bearer {token}"})
        assert r2.status_code == 403

    async def test_options_unauthorized_fails(self, client):
        r = await client.get("/students/options")
        assert r.status_code == 401
