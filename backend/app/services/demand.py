import uuid
from datetime import date, datetime, timezone
from typing import Optional
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import (
    JobPosting, JobSkill, Skill, Region, Role, Sector,
    SkillEvidence,
)
from app.services.skill_matcher import normalize_skill_name, find_or_create_skill
from app.schemas import DemandSkillOut, DemandOut, SkillOut


# Configurable scoring weights — change here without rewriting app logic.
DEMAND_WEIGHTS = {
    "frequency": 0.50,
    "recency": 0.20,
    "role_relevance": 0.20,
    "sector_relevance": 0.10,
}

# Confidence thresholds based on number of relevant jobs.
CONFIDENCE_HIGH_MIN_JOBS = 30
CONFIDENCE_MEDIUM_MIN_JOBS = 10


def _compute_recency(posted: Optional[date], reference: date, window: str) -> float:
    if not posted:
        return 0.7
    if window == "30d":
        days_old = (reference - posted).days
        return max(0.0, 1.0 - (days_old / 30.0))
    if window == "90d":
        days_old = (reference - posted).days
        return max(0.0, 1.0 - (days_old / 90.0))
    if window == "6mo":
        days_old = (reference - posted).days
        return max(0.0, 1.0 - (days_old / 180.0))
    return 1.0  # all time


def _compute_role_relevance(job_role_id: Optional[uuid.UUID], target_role_id: Optional[uuid.UUID]) -> float:
    if not target_role_id or not job_role_id:
        return 1.0
    return 1.0 if job_role_id == target_role_id else 0.6


def _compute_sector_relevance(job_sector_id: Optional[uuid.UUID], target_sector_id: Optional[uuid.UUID]) -> float:
    if not target_sector_id or not job_sector_id:
        return 1.0
    return 1.0 if job_sector_id == target_sector_id else 0.7


def compute_demand_score(
    frequency: float,
    recency: float,
    role_relevance: float,
    sector_relevance: float,
    weights: dict | None = None,
) -> float:
    w = weights or DEMAND_WEIGHTS
    return (
        w["frequency"] * frequency
        + w["recency"] * recency
        + w["role_relevance"] * role_relevance
        + w["sector_relevance"] * sector_relevance
    )


def demand_confidence_flag(job_count: int) -> str:
    if job_count >= CONFIDENCE_HIGH_MIN_JOBS:
        return "high"
    if job_count >= CONFIDENCE_MEDIUM_MIN_JOBS:
        return "medium"
    return "low"


def _region_is_small(region: Region) -> bool:
    # Treat regions with very few direct jobs as "small city" candidates.
    # In MVP we infer from presence of parent_region_id or alias; admins can set confidence_default.
    return region.confidence_default in ("medium", "low")


async def build_demand_context(
    db: AsyncSession,
    region_id: Optional[uuid.UUID] = None,
    role_id: Optional[uuid.UUID] = None,
    sector_id: Optional[uuid.UUID] = None,
    time_window: str = "all",
    use_fallback: bool = False,
) -> dict:
    """
    Build demand data for a given region/role/sector/time_window.
    If region data is sparse, attempt smaller->broader fallback if use_fallback=True.
    """
    region_result = None
    region = None
    if region_id:
        rr = await db.execute(select(Region).where(Region.id == region_id))
        region = rr.scalar_one_or_none()
        region_result = rr

    reference_date = datetime.now(timezone.utc).date()
    # Demand is computed from the available dataset (curated/demo jobs included).
    # Demo data is labelled in the response, never presented as live market data.
    jobs_query = select(JobPosting)
    if region_id:
        jobs_query = jobs_query.where(JobPosting.region_id == region_id)
    if role_id:
        jobs_query = jobs_query.where(JobPosting.role_id == role_id)
    if sector_id:
        jobs_query = jobs_query.where(JobPosting.sector_id == sector_id)

    if time_window != "all":
        cutoff = None
        if time_window == "30d":
            cutoff = reference_date.fromordinal(reference_date.toordinal() - 30)
        elif time_window == "90d":
            cutoff = reference_date.fromordinal(reference_date.toordinal() - 90)
        elif time_window == "6mo":
            cutoff = reference_date.fromordinal(reference_date.toordinal() - 180)
        if cutoff:
            jobs_query = jobs_query.where(JobPosting.posted_date >= cutoff)

    jobs_result = await db.execute(jobs_query.order_by(JobPosting.posted_date.desc()))
    jobs = list(jobs_result.scalars().all())
    total_jobs = len(jobs)
    demo_flags = [bool(j.is_demo) for j in jobs]

    # Attribute collection per skill
    skill_freq: dict[uuid.UUID, int] = {}
    skill_recency_num: dict[uuid.UUID, float] = {}
    skill_role_rel_num: dict[uuid.UUID, float] = {}
    skill_sector_rel_num: dict[uuid.UUID, float] = {}
    skill_job_count: dict[uuid.UUID, int] = {}

    for job in jobs:
        req = list(job.required_skills or [])
        opt = list(job.optional_skills or [])
        # required skills count fully, optional count half
        seen_in_job: dict[uuid.UUID, float] = {}
        for sname in req:
            norm = normalize_skill_name(sname)
            sk = await find_or_create_skill(db, norm)
            if not sk:
                continue
            seen_in_job[sk.id] = seen_in_job.get(sk.id, 0.0) + 1.0
        for sname in opt:
            norm = normalize_skill_name(sname)
            sk = await find_or_create_skill(db, norm)
            if not sk:
                continue
            seen_in_job[sk.id] = seen_in_job.get(sk.id, 0.0) + 0.5

        for sk_id, weight in seen_in_job.items():
            skill_freq[sk_id] = skill_freq.get(sk_id, 0) + weight
            skill_job_count[sk_id] = skill_job_count.get(sk_id, 0) + 1
            rec = _compute_recency(job.posted_date, reference_date, time_window)
            skill_recency_num[sk_id] = skill_recency_num.get(sk_id, 0.0) + rec
            role_rel = _compute_role_relevance(job.role_id, role_id)
            skill_role_rel_num[sk_id] = skill_role_rel_num.get(sk_id, 0.0) + role_rel
            sec_rel = _compute_sector_relevance(job.sector_id, sector_id)
            skill_sector_rel_num[sk_id] = skill_sector_rel_num.get(sk_id, 0.0) + sec_rel

    # Build evidence rows + demand output
    if total_jobs == 0 and region and use_fallback:
        return await _fallback_region(db, region, role_id, sector_id, time_window)

    # Determine fallback for small city: if total_jobs is very low, use parent region
    fallback_used = False
    if region and total_jobs < CONFIDENCE_MEDIUM_MIN_JOBS and region.parent_region_id:
        pr = await db.execute(select(Region).where(Region.id == region.parent_region_id))
        parent = pr.scalar_one_or_none()
        if parent:
            fallback_used, parent_jobs, parent_total = await _load_parent_region_jobs(
                db, parent.id, role_id, sector_id, time_window, reference_date
            )
            if parent_total > total_jobs or (total_jobs == 0 and fallback_used is False):
                # merge
                for j in parent_jobs:
                    if j not in jobs:
                        demo_flags.append(bool(j.is_demo))
                        req = list(j.required_skills or [])
                        opt = list(j.optional_skills or [])
                        seen_in_job: dict[uuid.UUID, float] = {}
                        for sname in req:
                            norm = normalize_skill_name(sname)
                            sk = await find_or_create_skill(db, norm)
                            if sk:
                                seen_in_job[sk.id] = seen_in_job.get(sk.id, 0.0) + 1.0
                        for sname in opt:
                            norm = normalize_skill_name(sname)
                            sk = await find_or_create_skill(db, norm)
                            if sk:
                                seen_in_job[sk.id] = seen_in_job.get(sk.id, 0.0) + 0.5
                        for sk_id, weight in seen_in_job.items():
                            skill_freq[sk_id] = skill_freq.get(sk_id, 0) + weight
                            skill_job_count[sk_id] = skill_job_count.get(sk_id, 0) + 1
                            rec = _compute_recency(j.posted_date, reference_date, time_window)
                            skill_recency_num[sk_id] = skill_recency_num.get(sk_id, 0.0) + rec
                            role_rel = _compute_role_relevance(j.role_id, role_id)
                            skill_role_rel_num[sk_id] = skill_role_rel_num.get(sk_id, 0.0) + role_rel
                            sec_rel = _compute_sector_relevance(j.sector_id, sector_id)
                            skill_sector_rel_num[sk_id] = skill_sector_rel_num.get(sk_id, 0.0) + sec_rel
                total_jobs = len(jobs) + len(parent_jobs)
                fallback_used = True

    skills_out: list[DemandSkillOut] = []
    for sk_id, freq in skill_freq.items():
        n = skill_job_count.get(sk_id, 0)
        # Demand frequency = weighted skill mentions / total relevant jobs.
        frequency = freq / max(total_jobs, 1)
        # Recency / relevance are averaged over the jobs that mention the skill.
        recency_avg = (skill_recency_num.get(sk_id, 0.0) / n) if n else 0.0
        role_rel_avg = (skill_role_rel_num.get(sk_id, 0.0) / n) if n else 0.0
        sec_rel_avg = (skill_sector_rel_num.get(sk_id, 0.0) / n) if n else 0.0
        score = compute_demand_score(frequency, recency_avg, role_rel_avg, sec_rel_avg)

        sk_result = await db.execute(select(Skill).where(Skill.id == sk_id))
        skill = sk_result.scalar_one_or_none()
        if not skill:
            continue
        flag = demand_confidence_flag(job_count=skill_job_count.get(sk_id, 0) or int(frequency * total_jobs))
        if total_jobs == 0:
            flag = "low"

        job_count_for_skill = skill_job_count.get(sk_id, 0)

        evidence_detail = (
            f"Appears in {job_count_for_skill} of {total_jobs} relevant jobs "
            f"({frequency*100:.1f}% weighted frequency) in "
            f"{region.name if region else 'all regions'}."
        ) if total_jobs else "No data."

        skills_out.append(DemandSkillOut(
            skill_id=sk_id,
            skill=SkillOut.model_validate(skill),
            demand_score=float(score),
            demand_percent=float(frequency * 100),
            demand_frequency=float(frequency),
            demand_recency=float(recency_avg),
            demand_role_relevance=float(role_rel_avg),
            demand_sector_relevance=float(sec_rel_avg),
            job_count=job_count_for_skill,
            confidence=flag,
            time_window=time_window,
            evidence=evidence_detail,
        ))

    skills_out.sort(key=lambda x: -x.demand_score)

    flag = demand_confidence_flag(total_jobs)
    return {
        "region_id": region_id,
        "role_id": role_id,
        "sector_id": sector_id,
        "time_window": time_window,
        "confidence": flag,
        "total_jobs": total_jobs,
        "skills": skills_out,
        "is_demo": any(demo_flags),
        "evidence_note": (
            "Based on structured job postings in the dataset. "
            + ("Small-city fallback applied: data aggregated from broader region '" + (region.parent_region.name if region and region.parent_region_id else "parent") + "'." if fallback_used else "")
            + " Not real-time market data."
        ),
        "fallback_used": fallback_used,
    }


async def _load_parent_region_jobs(db, parent_id, role_id, sector_id, time_window, reference_date):
    jobs_query = select(JobPosting).where(JobPosting.region_id == parent_id)
    if role_id:
        jobs_query = jobs_query.where(JobPosting.role_id == role_id)
    if sector_id:
        jobs_query = jobs_query.where(JobPosting.sector_id == sector_id)
    if time_window != "all":
        cutoff = None
        if time_window == "30d":
            cutoff = reference_date.fromordinal(reference_date.toordinal() - 30)
        elif time_window == "90d":
            cutoff = reference_date.fromordinal(reference_date.toordinal() - 90)
        elif time_window == "6mo":
            cutoff = reference_date.fromordinal(reference_date.toordinal() - 180)
        if cutoff:
            jobs_query = jobs_query.where(JobPosting.posted_date >= cutoff)
    res = await db.execute(jobs_query)
    return True, res.scalars().all(), len(res.scalars().all())


async def _fallback_region(db, region, role_id, sector_id, time_window):
    """Fallback when no direct data: use parent region or all regions."""
    if region.parent_region_id:
        pr = await db.execute(select(Region).where(Region.id == region.parent_region_id))
        parent = pr.scalar_one_or_none()
        if parent:
            out = await build_demand_context(db, parent.id, role_id, sector_id, time_window, use_fallback=False)
            out["confidence"] = "medium"
            out["evidence_note"] = (
                "Low direct data for " + region.name + ". "
                "Using broader region '" + parent.name + "' as fallback. "
                "Treat as medium confidence."
            )
            out["region_id"] = region_id
            return out
    # last resort: all regions
    out = await build_demand_context(db, None, role_id, sector_id, time_window, use_fallback=False)
    out["confidence"] = "low"
    out["evidence_note"] = (
        "Insufficient regional data for " + (region.name if region else "selected region") + ". "
        "Using all-region aggregate with low confidence."
    )
    return out


async def upsert_skill_evidence(
    db: AsyncSession,
    skill_id: uuid.UUID,
    region_id: Optional[uuid.UUID] = None,
    role_id: Optional[uuid.UUID] = None,
    sector_id: Optional[uuid.UUID] = None,
    time_window: str = "all",
    frequency: float = 0.0,
    recency: float = 0.0,
    role_relevance: float = 0.0,
    sector_relevance: float = 0.0,
    job_count: int = 0,
    confidence: str = "high",
) -> SkillEvidence:
    result = await db.execute(
        select(SkillEvidence).where(
            and_(
                SkillEvidence.skill_id == skill_id,
                SkillEvidence.region_id == region_id,
                SkillEvidence.role_id == role_id,
                SkillEvidence.sector_id == sector_id,
                SkillEvidence.time_window == time_window,
            )
        )
    )
    existing = result.scalar_one_or_none()
    score = compute_demand_score(frequency, recency, role_relevance, sector_relevance)
    vals = dict(
        skill_id=skill_id,
        region_id=region_id,
        role_id=role_id,
        sector_id=sector_id,
        time_window=time_window,
        job_count=job_count,
        demand_frequency=frequency,
        demand_recency=recency,
        demand_role_relevance=role_relevance,
        demand_sector_relevance=sector_relevance,
        demand_score=score,
        confidence=confidence,
        calculated_at=datetime.now(timezone.utc),
    )
    if existing:
        for k, v in vals.items():
            setattr(existing, k, v)
        obj = existing
    else:
        obj = SkillEvidence(**vals)
        db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj
