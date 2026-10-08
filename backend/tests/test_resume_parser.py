import pytest
from app.services.resume_parser import extract_skills_from_text, _extract_candidates


class TestRuleBasedExtraction:
    def test_extract_from_text(self):
        text = "Developed REST APIs using Java Spring Boot and deployed applications using Docker."
        skills = extract_skills_from_text(text)
        names = {s["name"] for s in skills}
        assert "Java" in names or "Java" in str(names)
        assert "Spring Boot" in names
        assert "REST APIs" in names or "REST API" in names
        assert "Docker" in names

    def test_empty_text(self):
        assert extract_skills_from_text("") == []
        assert extract_skills_from_text(None if False else "") == []

    def test_aws_mentions(self):
        text = "Experience with AWS and Amazon Web Services"
        skills = extract_skills_from_text(text)
        names = {s["name"] for s in skills}
        assert "AWS" in names

    def test_confidence_high_for_common(self):
        text = "Used Docker, Kubernetes, AWS, and REST APIs"
        skills = extract_skills_from_text(text)
        by_name = {s["name"]: s for s in skills}
        assert by_name.get("Docker", {}).get("confidence", 0) >= 0.9
        assert by_name.get("AWS", {}).get("confidence", 0) >= 0.9
