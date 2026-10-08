import uuid
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import (
    User, JobPosting, Skill, Region, Role, Sector, SkillGap, StudentProfile, SkillEvidence,
)
from app.schemas import AdminStatisticsOut, RoleSelectionOut, DataQualityOut
from app.dependencies import get_current_admin

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/statistics", response_model=AdminStatisticsOut)
async def admin_statistics(
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_admin),
):
    students = await db.execute(select(User).where(User.role == "student"))
    total_students = len(students.scalars().all())

    jobs = await db.execute(select(JobPosting))
    total_jobs = len(jobs.scalars().all())

    skills = await db.execute(select(Skill).where(Skill.is_active == True))
    total_skills = len(skills.scalars().all())

    regions = await db.execute(select(Region).where(Region.is_active == True))
    total_regions = len(regions.scalars().all())

    roles = await db.execute(select(Role).where(Role.is_active == True))
    total_roles = len(roles.scalars().all())

    sectors = await db.execute(select(Sector).where(Sector.is_active == True))
    total_sectors = len(sectors.scalars().all())

    # Top demanded skills (from any evidence with high job_count)
    ev_result = await db.execute(
        select(SkillEvidence)
        .order_by(SkillEvidence.job_count.desc())
        .limit(10)
    )
    ev_rows = ev_result.scalars().all()
    top_skills = []
    for ev in ev_rows:
        sk_result = await db.execute(select(Skill).where(Skill.id == ev.skill_id))
        sk = sk_result.scalar_one_or_none()
        if sk:
            top_skills.append(
                {
                    "skill_id": sk.id,
                    "skill": {"id": sk.id, "name": sk.name, "category": sk.category, "description": sk.description, "aliases": sk.aliases or [], "related_skill_ids": sk.related_skill_ids or [], "is_active": sk.is_active},
                    "demand_score": ev.demand_score,
                    "demand_percent": ev.demand_frequency * 100,
                    "demand_frequency": ev.demand_frequency,
                    "demand_recency": ev.demand_recency,
                    "demand_role_relevance": ev.demand_role_relevance,
                    "demand_sector_relevance": ev.demand_sector_relevance,
                    "job_count": ev.job_count,
                    "confidence": ev.confidence,
                    "time_window": ev.time_window,
                    "evidence": None,
                    "is_demo": False,
                }
            )

    # Most selected roles (from student profiles)
    role_counts: dict[uuid.UUID, int] = {}
    sp_result = await db.execute(select(StudentProfile))
    for sp in sp_result.scalars().all():
        if sp.target_role_id:
            role_counts[sp.target_role_id] = role_counts.get(sp.target_role_id, 0) + 1
    most_selected = []
    for rid, cnt in sorted(role_counts.items(), key=lambda x: -x[1])[:10]:
        rr = await db.execute(select(Role).where(Role.id == rid))
        role = rr.scalar_one_or_none()
        if role:
            most_selected.append(RoleSelectionOut(role_id=role.id, role_name=role.name, count=cnt))

    # Average skill gaps per student (count gaps with status missing/partial)
    total_gaps = await db.execute(select(SkillGap))
    gaps = total_gaps.scalars().all()
    avg = (len(gaps) / max(total_students, 1)) if total_students else 0.0

    return AdminStatisticsOut(
        total_students=total_students,
        total_jobs=total_jobs,
        total_skills=total_skills,
        total_regions=total_regions,
        total_roles=total_roles,
        total_sectors=total_sectors,
        top_demanded_skills=top_skills,
        most_selected_roles=most_selected,
        average_skill_gaps=round(avg, 2),
        data_quality=None,
    )
