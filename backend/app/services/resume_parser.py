import os
from typing import List, Dict, Any


def extract_text_from_pdf(path: str) -> str:
    """Extract text from PDF. Falls back to empty string on failure."""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(path)
        parts = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                parts.append(t)
        return "\n".join(parts)
    except Exception:
        return ""


# Rule-based skill candidates for MVP/demo fallback.
# Expanded in production by the AI service abstraction.
_COMMON_TECH_SKILLS = [
    "Java", "Python", "JavaScript", "TypeScript", "C", "C++", "C#", "Go", "Rust", "Kotlin",
    "SQL", "NoSQL", "MongoDB", "PostgreSQL", "MySQL", "Oracle", "Redis", "Elasticsearch",
    "HTML", "CSS", "React", "Angular", "Vue.js", "Node.js", "Express", "Next.js",
    "Spring Boot", "Spring Framework", "Django", "Flask", "FastAPI", "ASP.NET",
    "REST APIs", "REST API", "GraphQL", "gRPC", "SOAP", "WebSockets",
    "Docker", "Kubernetes", "CI/CD", "Jenkins", "Git", "GitHub Actions", "GitHub",
    "AWS", "Amazon Web Services", "Azure", "Google Cloud", "GCP",
    "Linux", "Shell Scripting", "Bash", "Networking", "TCP/IP",
    "System Design", "Microservices", "Monolith", "Design Patterns",
    "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "Scikit-learn",
    "Data Analysis", "Data Visualization", "Pandas", "NumPy", "Excel",
    "Tableau", "Power BI", "Matplotlib", "Seaborn",
    "Natural Language Processing", "NLP", "Computer Vision", "Computer vision",
    "Statistics", "Probability", "Mathematics",
    "Cybersecurity", "Penetration Testing", "SIEM", "Firewalls", "IDS/IPS",
    "Mobile App Development", "Android", "iOS", "Flutter", "React Native",
    "Agile", "Scrum", "Jira", "Problem Solving", "Communication",
    "Git", "Version Control", "Testing", "Unit Testing", "Integration Testing",
    "DevOps", "Cloud", "Serverless", "Lambda", "Containers",
]


def _tokenize(text: str) -> List[str]:
    low = text.lower()
    return low.split()


def _extract_candidates(text: str) -> List[Dict[str, Any]]:
    lower = text.lower()
    found: Dict[str, Dict[str, Any]] = {}
    for skill in _COMMON_TECH_SKILLS:
        key = skill.lower()
        # match whole-word-ish and also handle multi-word mentions
        if key in lower:
            # rough confidence based on how "clean" the mention is
            confidence = 0.85
            if key in ("aws", "gcp", "azure", "linux", "docker", "kubernetes"):
                confidence = 0.94
            if key in ("java", "python", "sql", "typescript", "react", "node.js", "spring boot"):
                confidence = 0.95
            if key in ("rest api", "rest apis"):
                confidence = 0.92
            if key in ("machine learning", "deep learning", "computer vision", "natural language processing"):
                confidence = 0.9
            found[skill] = {"name": skill, "confidence": confidence, "source": "rule"}
    # More specific mentions can bump confidence
    for phrase, skill in [
        ("spring boot", "Spring Boot"),
        ("docker container", "Docker"),
        ("dockerfile", "Docker"),
        ("kubernetes cluster", "Kubernetes"),
        ("ci/cd pipeline", "CI/CD"),
        ("continuous integration", "CI/CD"),
        ("amazon web services", "AWS"),
        ("aws cloud", "AWS"),
        ("google cloud platform", "GCP"),
        ("microsoft azure", "Azure"),
        ("react app", "React"),
        ("node.js app", "Node.js"),
        ("postgresql database", "PostgreSQL"),
        ("mongodb database", "MongoDB"),
        ("redis cache", "Redis"),
        ("microservices architecture", "Microservices"),
        ("restful api", "REST APIs"),
        ("graphql api", "GraphQL"),
        ("tensorflow model", "TensorFlow"),
        ("pytorch model", "PyTorch"),
        ("pandas dataframe", "Pandas"),
        ("data visualization", "Data Visualization"),
        ("penetration test", "Penetration Testing"),
        ("siem tool", "SIEM"),
    ]:
        if phrase in lower:
            found[skill] = found.get(skill, {"name": skill, "confidence": 0.8, "source": "rule"})
            found[skill]["confidence"] = max(found[skill]["confidence"], 0.96)

    return sorted(found.values(), key=lambda x: -x["confidence"])


def extract_skills_from_text(text: str, use_ai: bool = False) -> List[Dict[str, Any]]:
    """
    Extract skills from resume text.
    If use_ai is True, the AI service layer may override. Otherwise rule-based.
    Returns list of {name, confidence, source}.
    """
    if not text or not text.strip():
        return []
    if use_ai:
        from app.services.ai_service import ai_extract_skills
        return ai_extract_skills(text)
    return _extract_candidates(text)
