import pytest


async def _register(client, email="itest@demo.local"):
    r = await client.post("/auth/register", json={
        "full_name": "Integration Student",
        "email": email,
        "password": "demo1234",
        "location": "Chennai",
    })
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


class TestDemandIntegration:
    async def test_chennai_backend_demand_percentages_are_relative_to_total_jobs(self, client):
        token = await _register(client)
        H = {"Authorization": f"Bearer {token}"}
        opts = (await client.get("/students/options", headers=H)).json()
        region = next(r for r in opts["regions"] if r["name"] == "Chennai")
        role = next(r for r in opts["roles"] if r["name"] == "Backend Developer")

        r = await client.get(f"/demand?region_id={region['id']}&role_id={role['id']}", headers=H)
        assert r.status_code == 200, r.text
        dem = r.json()

        assert dem["total_jobs"] > 0, "seeded Chennai backend jobs must be counted"
        assert dem["confidence"] in ("high", "medium", "low")
        assert dem["is_demo"] is True, "seed data must be flagged as demo"

        by_name = {s["skill"]["name"]: s for s in dem["skills"]}
        assert "Java" in by_name
        # Java is required by every seeded Chennai backend job.
        assert by_name["Java"]["demand_percent"] == pytest.approx(100.0)

        # Some skills must be below 100% - otherwise the denominator is wrong
        # (regression guard for dividing by the skill's own job count).
        below = [s for s in dem["skills"] if s["demand_percent"] < 100.0]
        assert below, "expected at least one skill not required by every job"

        # No demand percentage may exceed 100.
        assert all(0.0 <= s["demand_percent"] <= 100.0 for s in dem["skills"])

    async def test_skill_gaps_include_priority_and_reason(self, client):
        token = await _register(client, "itest2@demo.local")
        H = {"Authorization": f"Bearer {token}"}
        opts = (await client.get("/students/options", headers=H)).json()
        region = next(r for r in opts["regions"] if r["name"] == "Chennai")
        role = next(r for r in opts["roles"] if r["name"] == "Backend Developer")
        skills = {s["name"]: s["id"] for s in opts["skills"]}

        await client.put("/students/profile", headers=H, json={
            "preferred_region_id": region["id"], "target_role_id": role["id"],
        })
        await client.put("/students/skills", headers=H, json=[
            {"skill_id": skills["Java"], "level": "advanced", "source": "manual", "confidence": 1, "is_confirmed": True},
            {"skill_id": skills["SQL"], "level": "intermediate", "source": "manual", "confidence": 1, "is_confirmed": True},
        ])

        r = await client.get("/skill-gap", headers=H)
        assert r.status_code == 200, r.text
        gaps = r.json()
        assert gaps["gaps"], "expected gaps vs seeded demand"
        assert 0.0 <= gaps["readiness_percent"] <= 100.0

        missing = [g for g in gaps["gaps"] if g["status"] == "missing"]
        assert missing, "student is missing seeded skills like Docker/AWS"
        for g in missing:
            assert 0.0 <= g["priority_score"] <= 100.0
            assert g["priority_reason"], "every gap must have an explanation"

        matched = {g["skill"]["name"] for g in gaps["gaps"] if g["status"] == "matched"}
        assert "Java" in matched
        assert "SQL" in matched

    async def test_demand_path_route_matches_query_route(self, client):
        """Spec surface: GET /demand/{region}/{role} must behave like GET /demand?..."""
        token = await _register(client, "itest5@demo.local")
        H = {"Authorization": f"Bearer {token}"}
        opts = (await client.get("/students/options", headers=H)).json()
        region = next(r for r in opts["regions"] if r["name"] == "Chennai")
        role = next(r for r in opts["roles"] if r["name"] == "Backend Developer")

        by_path = await client.get(
            f"/demand/{region['id']}/{role['id']}", headers=H
        )
        by_query = await client.get(
            f"/demand?region_id={region['id']}&role_id={role['id']}", headers=H
        )
        assert by_path.status_code == 200, by_path.text
        assert by_query.status_code == 200, by_query.text
        a, b = by_path.json(), by_query.json()
        assert a["total_jobs"] == b["total_jobs"]
        assert [s["skill"]["name"] for s in a["skills"]] == [
            s["skill"]["name"] for s in b["skills"]
        ]

    async def test_projects_spec_routes(self, client):
        """Spec surface: GET/POST/PUT /projects."""
        token = await _register(client, "itest6@demo.local")
        H = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        created = await client.post("/projects", headers=H, json={
            "name": "Spec Project",
            "description": "Proof of Docker",
            "technologies": ["Docker", "REST APIs"],
            "github_url": "https://github.com/demo/spec",
            "status": "in_progress",
        })
        assert created.status_code == 201, created.text
        pid = created.json()["id"]
        assert created.json()["name"] == "Spec Project"

        listed = await client.get("/projects", headers=H)
        assert listed.status_code == 200, listed.text
        assert [p["id"] for p in listed.json()] == [pid]

        updated = await client.put(
            f"/projects/{pid}", headers=H, json={"status": "completed"}
        )
        assert updated.status_code == 200, updated.text
        assert updated.json()["status"] == "completed"

    async def test_add_and_remove_student_skill(self, client):
        token = await _register(client, "itest7@demo.local")
        H = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        opts = (await client.get("/students/options", headers=H)).json()
        docker = next(s for s in opts["skills"] if s["name"] == "Docker")

        added = await client.put("/students/skills", headers=H, json=[
            {"skill_id": docker["id"], "level": "beginner", "source": "manual", "confidence": 1, "is_confirmed": True},
        ])
        assert added.status_code == 200, added.text
        assert docker["id"] in {s["skill_id"] for s in added.json()}

        deleted = await client.delete(f"/students/skills/{docker['id']}", headers=H)
        assert deleted.status_code == 204, deleted.text

        after = await client.get("/students/skills", headers=H)
        assert docker["id"] not in {s["skill_id"] for s in after.json()}

    async def test_update_me_updates_personal_info(self, client):
        token = await _register(client, "itest3@demo.local")
        H = {"Authorization": f"Bearer {token}"}
        r = await client.put("/auth/me", headers=H, json={
            "college": "Updated College", "department": "IT", "degree": "B.E",
            "graduation_year": 2027, "location": "Coimbatore",
        })
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["college"] == "Updated College"
        assert body["location"] == "Coimbatore"
        assert body["graduation_year"] == 2027

    async def test_roadmap_generation_produces_six_weeks(self, client):
        token = await _register(client, "itest4@demo.local")
        H = {"Authorization": f"Bearer {token}"}
        opts = (await client.get("/students/options", headers=H)).json()
        region = next(r for r in opts["regions"] if r["name"] == "Chennai")
        role = next(r for r in opts["roles"] if r["name"] == "Backend Developer")
        me = (await client.get("/auth/me", headers=H)).json()

        await client.put("/students/profile", headers=H, json={
            "preferred_region_id": region["id"], "target_role_id": role["id"],
        })
        r = await client.post("/roadmap/generate", headers=H, json={
            "user_id": me["id"], "role_id": role["id"], "region_id": region["id"], "weeks": 6,
        })
        assert r.status_code == 201, r.text
        rm = r.json()
        assert len(rm["items"]) == 6
        weeks = [i["week_number"] for i in rm["items"]]
        assert weeks == [1, 2, 3, 4, 5, 6]

        # every item carries LEARN/BUILD/PROVE fields
        for item in rm["items"]:
            assert item["learning_objective"]
            assert item["project_task"]
            assert item["expected_output"]
            assert item["learn_status"] == "pending"
