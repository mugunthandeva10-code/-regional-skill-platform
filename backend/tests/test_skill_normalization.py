import pytest
from app.services.skill_matcher import normalize_skill_name


class TestNormalizeSkillName:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("aws", "AWS"),
            ("Amazon Web Services", "AWS"),
            ("AWS Cloud", "AWS"),
            ("google cloud platform", "Google Cloud"),
            ("GCP", "Google Cloud"),
            ("microsoft azure", "Azure"),
            ("rest api", "REST APIs"),
            ("rest apis", "REST APIs"),
            ("RESTful API", "REST APIs"),
            ("spring boot", "Spring Boot"),
            ("spring framework", "Spring Boot"),
            ("docker container", "Docker"),
            ("k8s", "Kubernetes"),
            ("ci/cd", "CI/CD"),
            ("continuous integration", "CI/CD"),
            ("machine learning", "Machine Learning"),
            ("scikit-learn", "Scikit-learn"),
            ("scikit learn", "Scikit-learn"),
            ("postgres", "PostgreSQL"),
            ("postgresql", "PostgreSQL"),
            ("reactjs", "React"),
            ("react.js", "React"),
            ("nodejs", "Node.js"),
            ("node.js", "Node.js"),
            ("typescript", "TypeScript"),
            ("c#", "C#"),
            ("python", "Python"),
            ("java", "Java"),
            ("sql", "SQL"),
        ],
    )
    def test_normalization(self, raw, expected):
        assert normalize_skill_name(raw) == expected

    def test_empty_returns_empty(self):
        assert normalize_skill_name("") == ""
        assert normalize_skill_name(None if False else "") == ""

    def test_title_case_canonical(self):
        assert normalize_skill_name("AWS") == "AWS"
        assert normalize_skill_name("Python") == "Python"
