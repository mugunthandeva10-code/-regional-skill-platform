"""
AI Service Abstraction
----------------------
The business logic (regional demand, skill gaps) is driven by structured data,
NOT by the LLM. The AI layer is used for:
- resume skill extraction (optional)
- skill normalization suggestions
- explanation text
- roadmap text personalization
- project recommendation text

Provider is configurable via settings.llm_provider. If unset or unreachable,
the system falls back to rule-based / predefined templates and never invents
job statistics.
"""
import os
from typing import List, Dict, Any, Optional
from app.config import get_settings

settings = get_settings()

# ---------------------------------------------------------------------------
# Provider abstraction
# ---------------------------------------------------------------------------

class BaseAIService:
    async def extract_skills(self, text: str, existing_skills: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        raise NotImplementedError

    async def explain_recommendation(self, skill: str, demand: Dict[str, Any], gap: Dict[str, Any], reason: str) -> str:
        raise NotImplementedError

    async def generate_roadmap_text(self, target_role: str, region: str, top_skills: List[str], gaps: List[Dict[str, Any]]) -> str:
        raise NotImplementedError

    async def generate_project_recommendation(self, skill: str, context: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError


class DemoAIService(BaseAIService):
    """Fully local, deterministic fallback. Never claims real-time data."""

    async def extract_skills(self, text: str, existing_skills: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        # Delegate to rule-based extractor (already imported by resume_parser)
        from app.services.resume_parser import extract_skills_from_text
        return extract_skills_from_text(text)

    async def explain_recommendation(self, skill: str, demand: Dict[str, Any], gap: Dict[str, Any], reason: str) -> str:
        lines = [
            f"WHY {skill}?",
            "",
        ]
        freq = demand.get("demand_frequency", 0) or 0
        role_rel = demand.get("demand_role_relevance", 1) or 1
        lines.append(f"- Appears in {freq*100:.0f}% of relevant jobs for your target role and region.")
        lines.append("- This skill is part of the structured regional demand dataset, not an AI guess.")
        if gap.get("gap_severity") == "missing":
            lines.append("- You currently do not have this skill in your profile.")
        elif gap.get("gap_severity") == "partial":
            lines.append("- You have some exposure to this skill but are not yet advanced.")
        if reason:
            lines.append(f"- Reason: {reason}.")
        lines.append("- Recommended action: add to your roadmap and build a small project to prove it.")
        return "\n".join(lines)

    async def generate_roadmap_text(self, target_role: str, region: str, top_skills: List[str], gaps: List[Dict[str, Any]]) -> str:
        return DEMO_ROADMAP_NOTE.format(
            region=region, target_role=target_role,
            gaps=", ".join(g.get("skill", "?") for g in gaps),
        )

    async def generate_project_recommendation(self, skill: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return DEMO_PROJECT_RECOMMENDATIONS.get(skill.lower(), {
            "name": f"{skill} Practice Project",
            "description": f"Build a small project demonstrating {skill}.",
            "technologies": [skill, "Git"],
            "proof_required": ["GitHub link", "Short explanation"],
        })


class OpenAISIService(BaseAIService):
    """Optional OpenAI/LiteLLM-backed service. Safe: never invents job stats."""

    def _client(self):
        # Lazy import so the app still starts without litellm installed.
        try:
            import litellm
            return litellm
        except Exception:
            return None

    async def extract_skills(self, text: str, existing_skills: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        client = self._client()
        if not client or not settings.openai_api_key:
            from app.services.resume_parser import extract_skills_from_text
            return extract_skills_from_text(text)
        try:
            system = (
                "You extract technical and professional skills from the resume text. "
                "Return ONLY a JSON array of objects with keys: name, confidence (0-1), source='ai'. "
                "Normalize skill names to canonical forms (e.g., 'AWS', 'REST APIs', 'Spring Boot'). "
                "Do not invent skills not present in the text. Do not include soft skills unless clearly technical."
            )
            user = f"Resume text:\n\n{text}"
            resp = client.completion(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url or "https://api.openai.com/v1",
                max_tokens=1024,
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            content = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
            import json
            parsed = json.loads(content)
            items = parsed.get("skills", [])
            return items
        except Exception:
            # Fail closed: fall back to rule-based, never invent.
            from app.services.resume_parser import extract_skills_from_text
            return extract_skills_from_text(text)

    async def explain_recommendation(self, skill: str, demand: Dict[str, Any], gap: Dict[str, Any], reason: str) -> str:
        # Use a constrained prompt that cannot invent demand numbers.
        freq = demand.get("demand_frequency", 0) or 0
        pct = freq * 100
        client = self._client()
        if not client or not settings.openai_api_key:
            from app.services.ai_service import DemoAIService
            return await DemoAIService().explain_recommendation(skill, demand, gap, reason)
        try:
            prompt = (
                "Write a short, honest explanation answering 'Why should I learn this skill?'. "
                "Use only the supplied numbers. Do not invent new statistics. "
                "If evidence is insufficient, say so.\n\n"
                f"Skill: {skill}\n"
                f"Demand frequency: {freq:.2f} ({pct:.0f}% of relevant jobs)\n"
                f"Gap severity: {gap.get('gap_severity','unknown')}\n"
                f"Your current level: {gap.get('student_level','unknown')}\n"
                f"Extra reason: {reason or 'none'}\n"
                f"Is demo data: {demand.get('is_demo', False)}\n"
            )
            resp = client.completion(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url or "https://api.openai.com/v1",
                max_tokens=512,
                temperature=0.2,
            )
            return resp.get("choices", [{}])[0].get("message", {}).get("content", "").strip() or (
                f"WHY {skill}?\n\n- Appears in {pct:.0f}% of relevant jobs for your target role and region.\n"
                f"- You currently do not have this skill.\n- Recommended action: add to roadmap and build a project."
            )
        except Exception:
            from app.services.ai_service import DemoAIService
            return await DemoAIService().explain_recommendation(skill, demand, gap, reason)

    async def generate_roadmap_text(self, target_role: str, region: str, top_skills: List[str], gaps: List[Dict[str, Any]]) -> str:
        client = self._client()
        if not client or not settings.openai_api_key:
            from app.services.ai_service import DemoAIService
            return await DemoAIService().generate_roadmap_text(target_role, region, top_skills, gaps)
        # Keep it minimal and grounded.
        return DEMO_ROADMAP_NOTE.format(
            region=region, target_role=target_role,
            gaps=", ".join(g.get("skill", "?") for g in gaps),
        )

    async def generate_project_recommendation(self, skill: str, context: Dict[str, Any]) -> Dict[str, Any]:
        skill_key = skill.lower()
        if skill_key in DEMO_PROJECT_RECOMMENDATIONS:
            return DEMO_PROJECT_RECOMMENDATIONS[skill_key]
        client = self._client()
        if not client or not settings.openai_api_key:
            return {
                "name": f"{skill} Practice Project",
                "description": f"Build a small project demonstrating {skill}.",
                "technologies": [skill, "Git"],
                "proof_required": ["GitHub link", "Short explanation"],
            }
        # Bounded prompt.
        try:
            prompt = (
                "Suggest one small portfolio project name, a 1-sentence description, the technologies to use, "
                "and 2 proof requirements. Return JSON: {name, description, technologies[list], proof_required[list]}. "
                f"Skill to demonstrate: {skill}"
            )
            resp = client.completion(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url or "https://api.openai.com/v1",
                max_tokens=512,
                temperature=0.3,
            )
            import json
            content = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
            parsed = json.loads(content)
            return parsed
        except Exception:
            return {
                "name": f"{skill} Practice Project",
                "description": f"Build a small project demonstrating {skill}.",
                "technologies": [skill, "Git"],
                "proof_required": ["GitHub link", "Short explanation"],
            }


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

def get_ai_service() -> BaseAIService:
    if settings.llm_provider and settings.llm_provider.lower() in ("openai", "litellm", "azure"):
        return OpenAISIService()
    return DemoAIService()


# ---------------------------------------------------------------------------
# Demo templates
# ---------------------------------------------------------------------------

DEMO_ROADMAP_NOTE = """
Roadmap for {target_role} in {region}.

Your top priority gaps: {gaps}.

This roadmap is generated from your skill gaps and regional demand. It is a starting point;
update it as you progress. Each week has LEARN → BUILD → PROVE stages and a concrete project
task. Completion is tracked per stage.

Note: This is DEMO DATA. Regional demand is based on the curated dataset, not live market feeds.
"""

DEMO_PROJECT_RECOMMENDATIONS: Dict[str, Dict[str, Any]] = {
    "docker": {
        "name": "Containerized Student Attendance API",
        "description": "Containerize a REST API and run it with Docker, demonstrating container images, build, and runtime.",
        "technologies": ["Docker", "REST APIs", "PostgreSQL"],
        "proof_required": ["GitHub link", "Screenshot of docker ps", "Short explanation"],
    },
    "aws": {
        "name": "Deploy REST API to Cloud",
        "description": "Deploy a containerized or zip-based service to a cloud platform and document the deployment.",
        "technologies": ["AWS", "Docker", "REST APIs"],
        "proof_required": ["Demo link or screenshot", "Short explanation of architecture"],
    },
    "system design": {
        "name": "System Design Document + Mini Service",
        "description": "Document a small system design for a real-world feature and implement the core service.",
        "technologies": ["System Design", "REST APIs", "Database"],
        "proof_required": ["Design doc (PDF/Markdown)", "GitHub link", "Short explanation"],
    },
    "kubernetes": {
        "name": "Deploy App to Kubernetes",
        "description": "Write a basic deployment/service YAML and run a containerized app on a local K8s cluster.",
        "technologies": ["Kubernetes", "Docker", "REST APIs"],
        "proof_required": ["GitHub link", "Screenshot of pods", "Short explanation"],
    },
    "ci/cd": {
        "name": "CI/CD Pipeline for a Small Service",
        "description": "Set up a pipeline that builds and tests a small service on push.",
        "technologies": ["CI/CD", "Git", "Testing"],
        "proof_required": ["Pipeline screenshot", "GitHub link", "Short explanation"],
    },
    "react": {
        "name": "Interactive Frontend Dashboard",
        "description": "Build a small dashboard UI consuming a REST API and displaying key metrics.",
        "technologies": ["React", "REST APIs", "CSS"],
        "proof_required": ["Live demo link or screenshot", "GitHub link"],
    },
    "python": {
        "name": "Python Data Processing Script",
        "description": "Write a Python script that ingests, cleans, and summarizes a dataset.",
        "technologies": ["Python", "Pandas"],
        "proof_required": ["GitHub link", "Sample output"],
    },
    "machine learning": {
        "name": "ML Model Microservice",
        "description": "Wrap a simple ML model behind a REST endpoint and document evaluation.",
        "technologies": ["Machine Learning", "FastAPI", "Pandas"],
        "proof_required": ["GitHub link", "Demo link or curl example", "Short explanation"],
    },
    "sql": {
        "name": "Reporting Queries Project",
        "description": "Write and document a set of reporting SQL queries for a sample schema.",
        "technologies": ["SQL", "PostgreSQL"],
        "proof_required": ["SQL file", "Sample output", "Short explanation"],
    },
    "git": {
        "name": "Version-Controlled Portfolio",
        "description": "Structure a small project with branches, commits, and a clean README.",
        "technologies": ["Git", "GitHub"],
        "proof_required": ["GitHub link", "README"],
    },
}

# Singleton-like accessor used by other services
_ai_service: Optional[BaseAIService] = None


def ai_extract_skills(text: str, existing_skills: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    import asyncio
    svc = get_ai_service()
    try:
        return asyncio.run(svc.extract_skills(text, existing_skills))
    except RuntimeError:
        # In sync contexts (e.g., resume upload during sync code path), use run_in_executor-safe approach.
        return sync_extract(text, existing_skills)


def sync_extract(text: str, existing_skills: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    from app.services.resume_parser import extract_skills_from_text
    return extract_skills_from_text(text)
