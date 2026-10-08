import pytest
from app.services.roadmap import _pick_template, TEMPLATE_ROADMAPS
from app.services.ai_service import DEMO_PROJECT_RECOMMENDATIONS


class TestRoadmapTemplates:
    def test_backend_developer_template(self):
        tmpl = _pick_template("Backend Developer")
        assert len(tmpl) >= 6
        titles = [t["title"] for t in tmpl]
        assert any("REST API" in t for t in titles)
        assert any("Docker" in t for t in titles)
        assert any("AWS" in t or "Cloud" in t for t in titles)

    def test_fallback_to_backend(self):
        tmpl = _pick_template("NonExistent Role")
        assert len(tmpl) >= 6

    def test_all_common_roles_have_templates(self):
        for role in ["Backend Developer", "Frontend Developer", "Full Stack Developer",
                     "Data Analyst", "Data Scientist", "AI/ML Engineer",
                     "DevOps Engineer", "Cybersecurity Analyst", "Cloud Engineer",
                     "Mobile App Developer"]:
            tmpl = _pick_template(role)
            assert len(tmpl) >= 1, f"No template for {role}"


class TestProjectRecommendations:
    def test_docker_recommendation(self):
        rec = DEMO_PROJECT_RECOMMENDATIONS["docker"]
        assert rec["name"]
        assert "Docker" in rec["technologies"]
        assert len(rec["proof_required"]) >= 1

    def test_aws_recommendation(self):
        rec = DEMO_PROJECT_RECOMMENDATIONS["aws"]
        assert rec["name"]
        assert "AWS" in rec["technologies"]

    def test_demo_service_provides_fallback_for_unknown_skill(self):
        import asyncio
        from app.services.ai_service import DemoAIService
        svc = DemoAIService()
        rec = asyncio.run(svc.generate_project_recommendation("nonexistent-skill", {}))
        assert rec.get("name")
        assert rec.get("technologies")
