import re
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Skill, SkillAlias


def normalize_skill_name(raw: str) -> str:
    """
    Normalize a free-text skill mention to a canonical skill name.
    This is intentionally rule-driven so the system is predictable and auditable.
    """
    if not raw:
        return ""
    s = raw.strip()
    # common normalizations
    mappings = {
        "aws": "AWS",
        "amazon web services": "AWS",
        "aws cloud": "AWS",
        "amazon web service": "AWS",
        "azur": "Azure",
        "microsoft azure": "Azure",
        "gcp": "Google Cloud",
        "google cloud platform": "Google Cloud",
        "google cloud": "Google Cloud",
        "rest apis": "REST APIs",
        "rest api": "REST APIs",
        "restful api": "REST APIs",
        "restful apis": "REST APIs",
        "graphql": "GraphQL",
        "spring boot": "Spring Boot",
        "spring framework": "Spring Boot",
        "docker": "Docker",
        "docker container": "Docker",
        "kubernetes": "Kubernetes",
        "k8s": "Kubernetes",
        "ci/cd": "CI/CD",
        "continuous integration": "CI/CD",
        "machine learning": "Machine Learning",
        "deep learning": "Deep Learning",
        "tensor flow": "TensorFlow",
        "pytorch": "PyTorch",
        "scikit-learn": "Scikit-learn",
        "scikit learn": "Scikit-learn",
        "pandas": "Pandas",
        "numpy": "NumPy",
        "postgresql": "PostgreSQL",
        "postgres": "PostgreSQL",
        "mongodb": "MongoDB",
        "redis": "Redis",
        "elasticsearch": "Elasticsearch",
        "react.js": "React",
        "reactjs": "React",
        "react": "React",
        "vue.js": "Vue.js",
        "vuejs": "Vue.js",
        "angular.js": "Angular",
        "angularjs": "Angular",
        "node.js": "Node.js",
        "nodejs": "Node.js",
        "next.js": "Next.js",
        "nextjs": "Next.js",
        "django": "Django",
        "flask": "Flask",
        "fastapi": "FastAPI",
        "asp.net": "ASP.NET",
        "sql": "SQL",
        "structured query language": "SQL",
        "typescript": "TypeScript",
        "ts": "TypeScript",
        "javascript": "JavaScript",
        "js": "JavaScript",
        "html": "HTML",
        "html5": "HTML",
        "css": "CSS",
        "css3": "CSS",
        "c#": "C#",
        "csharp": "C#",
        "c++": "C++",
        "c": "C",
        "go": "Go",
        "golang": "Go",
        "rust": "Rust",
        "kotlin": "Kotlin",
    }
    low = s.lower()
    if low in mappings:
        return mappings[low]
    # title case canonical names are preferred if exact match
    if s in [m for m in mappings.values()]:
        return s
    # acronyms already handled
    # fallback: capitalize each word
    return " ".join(w.capitalize() if w.islower() else w for w in s.split())


async def find_or_create_skill(db: AsyncSession, normalized: str) -> Skill | None:
    """Find an existing active skill by name or alias; otherwise return None (caller may create)."""
    # exact name match
    result = await db.execute(
        select(Skill).where(Skill.name == normalized, Skill.is_active == True)
    )
    skill = result.scalar_one_or_none()
    if skill:
        return skill

    # alias match
    result = await db.execute(
        select(SkillAlias.skill_id, Skill)
        .join(Skill, Skill.id == SkillAlias.skill_id)
        .where(SkillAlias.alias.ilike(normalized), Skill.is_active == True)
    )
    row = result.first()
    if row:
        return row[1]

    # fuzzy: check whether the normalized name overlaps an alias
    result = await db.execute(
        select(SkillAlias.alias, Skill)
        .join(Skill, Skill.id == SkillAlias.skill_id)
        .where(Skill.is_active == True)
    )
    for alias, skill in result.all():
        if not alias:
            continue
        if normalized.lower() in alias.lower() or alias.lower() in normalized.lower():
            return skill
    return None


async def find_skill_by_name(db: AsyncSession, name: str) -> Skill | None:
    skill = await find_or_create_skill(db, name)
    return skill
