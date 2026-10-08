import pytest
from app.models import User


class TestAuth:
    async def test_register_and_login(self, client):
        # register
        r = await client.post("/auth/register", json={
            "full_name": "Demo Student",
            "email": "student@demo.local",
            "password": "demo1234",
            "college": "Demo College",
            "department": "CSE",
            "degree": "B.Tech",
            "graduation_year": 2026,
            "location": "Chennai",
        })
        assert r.status_code == 201
        data = r.json()
        assert data["access_token"]
        assert data["user"]["email"] == "student@demo.local"
        assert data["user"]["role"] == "student"
        token = data["access_token"]

        # me
        r2 = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r2.status_code == 200
        assert r2.json()["email"] == "student@demo.local"

        # login again
        r3 = await client.post("/auth/login", json={"email": "student@demo.local", "password": "demo1234"})
        assert r3.status_code == 200
        assert r3.json()["user"]["email"] == "student@demo.local"

    async def test_invalid_login(self, client):
        r = await client.post("/auth/login", json={"email": "nope@demo.local", "password": "wrong"})
        assert r.status_code == 401

    async def test_duplicate_registration(self, client):
        await client.post("/auth/register", json={
            "full_name": "A", "email": "dup@demo.local", "password": "demo1234"
        })
        r = await client.post("/auth/register", json={
            "full_name": "B", "email": "dup@demo.local", "password": "demo1234"
        })
        assert r.status_code == 400
