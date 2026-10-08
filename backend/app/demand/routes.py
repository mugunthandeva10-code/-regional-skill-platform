import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import User
from app.schemas import DemandOut, DemandQuery, DataQualityOut
from app.dependencies import get_current_user, get_current_admin
from app.services.demand import build_demand_context
from app.services.jobs import list_jobs

router = APIRouter(tags=["demand"])


@router.get("/demand", response_model=DemandOut)
async def get_demand(
    region_id: Optional[uuid.UUID] = None,
    role_id: Optional[uuid.UUID] = None,
    sector_id: Optional[uuid.UUID] = None,
    time_window: str = "all",
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ctx = await build_demand_context(
        db, region_id, role_id, sector_id, time_window
    )
    skills = ctx.get("skills", [])[:limit]
    return DemandOut(
        region_id=ctx.get("region_id"),
        role_id=ctx.get("role_id"),
        sector_id=ctx.get("sector_id"),
        time_window=ctx.get("time_window", "all"),
        confidence=ctx.get("confidence", "low"),
        total_jobs=ctx.get("total_jobs", 0),
        skills=skills,
        evidence_note=ctx.get("evidence_note", ""),
        is_demo=bool(ctx.get("is_demo", False)),
    )


@router.get("/demand/{region_id}/{role_id}", response_model=DemandOut)
async def get_demand_for_region_role(
    region_id: uuid.UUID,
    role_id: uuid.UUID,
    sector_id: Optional[uuid.UUID] = None,
    time_window: str = "all",
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Spec-defined convenience route: GET /demand/{region}/{role}."""
    ctx = await build_demand_context(
        db, region_id, role_id, sector_id, time_window
    )
    skills = ctx.get("skills", [])[:limit]
    return DemandOut(
        region_id=ctx.get("region_id"),
        role_id=ctx.get("role_id"),
        sector_id=ctx.get("sector_id"),
        time_window=ctx.get("time_window", "all"),
        confidence=ctx.get("confidence", "low"),
        total_jobs=ctx.get("total_jobs", 0),
        skills=skills,
        evidence_note=ctx.get("evidence_note", ""),
        is_demo=bool(ctx.get("is_demo", False)),
    )


@router.get("/admin/data-quality", response_model=DataQualityOut)
async def get_data_quality(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    from app.models import JobPosting, Skill
    total = await db.execute(select(JobPosting))
    total_jobs = len(total.scalars().all())
    with_skills = await db.execute(
        select(JobPosting).where(JobPosting.required_skills != None, JobPosting.required_skills != [])
    )
    jobs_with = len(with_skills.scalars().all())
    skills_count = await db.execute(select(Skill).where(Skill.is_active == True))
    unique = len(skills_count.scalars().all())
    pct = (jobs_with / max(total_jobs, 1)) * 100.0
    confidence = "low" if total_jobs < 20 else ("medium" if total_jobs < 100 else "high")
    has_demo = await db.execute(select(JobPosting).where(JobPosting.is_demo == True))
    is_demo_data = len(has_demo.scalars().all()) > 0
    return DataQualityOut(
        jobs_analyzed=total_jobs,
        jobs_with_skill_extraction=jobs_with,
        unique_skills=unique,
        last_data_refresh=None,
        percentage_with_extracted_skills=round(pct, 1),
        confidence_level=confidence,
        is_demo_data=is_demo_data,
        note="Demo datasets are clearly labelled. Regional demand is computed from the structured job dataset, not live market feeds." if is_demo_data else "",
    )
