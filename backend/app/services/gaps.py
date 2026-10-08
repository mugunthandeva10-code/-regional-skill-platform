import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import (
    User, StudentSkill, Skill, SkillGap, SkillEvidence,
)
from app.schemas import (
    SkillGapOut, SkillGapList, DemandSkillOut,
)
from app.services.demand import compute_demand_score, demand_confidence_flag


# Priority formula components, configurable.
PRIORITY_WEIGHTS = {
    "demand": 0.40,
    "role_relevance": 0.20,
    "gap_severity": 0.25,
    "confidence": 0.15,
}


def _gap_severity(student_level: str, required_level: str = "intermediate") -> float:
    levels = {"none": 0.0, "beginner": 0.4, "intermediate": 0.7, "advanced": 1.0}
    sl = levels.get(student_level, 0.0)
    rl = levels.get(required_level, 0.7)
    if sl >= rl:
        return 0.0  # not a gap
    return (rl - sl) / rl  # 0..1


def _student_gap_status(student_level: str) -> str:
    if student_level == "none":
        return "missing"
    if student_level == "beginner":
        return "partial"
    return "partial"  # intermediate+ but still tracked


def priority_score(
    demand: float,
    role_relevance: float,
    gap_severity: float,
    confidence: float,
    weights: dict | None = None,
) -> float:
    w = weights or PRIORITY_WEIGHTS
    raw = (
        w["demand"] * demand
        + w["role_relevance"] * role_relevance
        + w["gap_severity"] * gap_severity
        + w["confidence"] * confidence
    )
    return round(min(100.0, max(0.0, raw * 100.0)), 1)


def build_reason(
    skill: str,
    demand: DemandSkillOut,
    student_level: str,
    status: str,
    role_relevance: float,
    confidence: float,
) -> str:
    freq_pct = round(demand.demand_percent, 1)
    lines = [
        f"- Required by {freq_pct}% of relevant jobs in your region/role.",
    ]
    if status == "missing":
        lines.append("- You do not currently have this skill.")
    elif status == "partial":
        lines.append(f"- You have {student_level} level; target is intermediate+.")
    else:
        lines.append("- Already at or above target level.")
    if role_relevance >= 0.9:
        lines.append("- Highly relevant to your target role.")
    elif role_relevance >= 0.6:
        lines.append("- Relevant to your target role.")
    lines.append(f"- Data confidence: {demand.confidence}.")
    lines.append("- Recommended action: add to your learning roadmap and build a project to prove it.")
    return "\n".join(lines)


async def analyze_skill_gaps(
    db: AsyncSession,
    user: User,
    region_id: Optional[uuid.UUID] = None,
    role_id: Optional[uuid.UUID] = None,
    sector_id: Optional[uuid.UUID] = None,
    time_window: str = "all",
) -> SkillGapList:
    """
    Compare market-required skills (from demand) vs student skills.
    Classifies MATCHED / PARTIAL / MISSING and assigns priority.
    """
    # Load student skills
    result = await db.execute(
        select(StudentSkill)
        .where(StudentSkill.user_id == user.id)
        .where(StudentSkill.is_confirmed == True)
    )
    student_rows = result.scalars().all()
    student_levels: dict[uuid.UUID, str] = {s.skill_id: s.level for s in student_rows}
    student_conf: dict[uuid.UUID, float] = {s.skill_id: s.confidence for s in student_rows}

    # Load demand context
    from app.services.demand import build_demand_context
    ctx = await build_demand_context(db, region_id, role_id, sector_id, time_window)
    demand_skills = ctx.get("skills", [])

    # Map demand skill -> student level/skill id
    gaps: List[SkillGapOut] = []
    matched_count = 0
    total_demand_skills = len(demand_skills)

    for d in demand_skills:
        sk_id = d.skill_id
        student_level = student_levels.get(sk_id, "none")
        student_conf_val = student_conf.get(sk_id, 0.0)
        # Determine status
        if student_level == "none":
            status = "missing"
        elif student_level in ("beginner",):
            status = "partial"
        else:
            # intermediate/advanced -> matched if demand_content
            status = "matched"

        sev = _gap_severity(student_level)
        role_rel = d.demand_role_relevance
        # demand frequency already normalized to 0..1
        demand_freq = d.demand_frequency
        conf = student_conf_val or (1.0 if status != "missing" else 0.5)
        # If demand confidence is low, reduce confinding of recommendation
        demand_conf_map = {"high": 1.0, "medium": 0.7, "low": 0.4}
        demand_conf = demand_conf_map.get(d.confidence, 0.5)
        combined_conf = (conf + demand_conf) / 2.0
        pri = priority_score(demand_freq, role_rel, sev, combined_conf)

        reason = build_reason(
            skill=d.skill.name,
            demand=d,
            student_level=student_level,
            status=status,
            role_relevance=role_rel,
            confidence=combined_conf,
        )

        gap_obj = SkillGap(
            user_id=user.id,
            skill_id=sk_id,
            status=status,
            market_demand=demand_freq,
            student_level=student_level,
            priority_score=pri,
            priority_reason=reason,
            calculated_at=datetime.now(timezone.utc),
        )
        # upsert
        existing = await db.execute(
            select(SkillGap).where(
                and_(SkillGap.user_id == user.id, SkillGap.skill_id == sk_id)
            )
        )
        prev = existing.scalar_one_or_none()
        if prev:
            prev.status = status
            prev.market_demand = demand_freq
            prev.student_level = student_level
            prev.priority_score = pri
            prev.priority_reason = reason
            prev.calculated_at = datetime.now(timezone.utc)
            gap_obj = prev
        else:
            db.add(gap_obj)
        await db.flush()
        await db.refresh(gap_obj, ["skill"])

        gaps.append(SkillGapOut(
            id=gap_obj.id,
            user_id=gap_obj.user_id,
            skill_id=gap_obj.skill_id,
            status=gap_obj.status,
            market_demand=gap_obj.market_demand,
            student_level=gap_obj.student_level,
            priority_score=gap_obj.priority_score,
            priority_reason=gap_obj.priority_reason,
            calculated_at=gap_obj.calculated_at,
            skill=gap_obj.skill,
            evidence=d,
        ))
        if status == "matched":
            matched_count += 1

    gaps.sort(key=lambda x: -x.priority_score)

    readiness = (matched_count / max(total_demand_skills, 1)) * 100.0
    coverage = (
        sum(1 for g in gaps if g.status in ("matched", "partial") and g.market_demand > 0)
        / max(total_demand_skills, 1)
    ) * 100.0

    await db.commit()
    return SkillGapList(
        user_id=user.id,
        gaps=gaps,
        readiness_percent=round(readiness, 1),
        demand_coverage_percent=round(coverage, 1),
    )
