import csv, io, uuid
from datetime import date, datetime, timezone
from typing import Optional
from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import (
    JobPosting, JobSkill, Skill, Region, Role, Sector,
)
from app.services.skill_matcher import normalize_skill_name, find_or_create_skill
from app.schemas import JobOut, JobCreate, JobUpdate


async def create_job(db: AsyncSession, data: JobCreate, is_demo: bool = False) -> JobOut:
    obj = JobPosting(
        **data.model_dump(),
        is_demo=is_demo,
    )
    db.add(obj)
    await db.flush()

    # Extract + normalize skills -> job_skills
    await _sync_job_skills(db, obj)

    await db.commit()
    await db.refresh(obj)
    return _job_to_out(db, obj)


async def update_job(db: AsyncSession, job_id: uuid.UUID, data: JobUpdate, is_demo: bool | None = None) -> JobOut:
    result = await db.execute(select(JobPosting).where(JobPosting.id == job_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise ValueError("Job not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    if is_demo is not None:
        obj.is_demo = is_demo
    await db.flush()
    await _sync_job_skills(db, obj)
    await db.commit()
    await db.refresh(obj)
    return _job_to_out(db, obj)


async def delete_job(db: AsyncSession, job_id: uuid.UUID) -> bool:
    result = await db.execute(select(JobPosting).where(JobPosting.id == job_id))
    obj = result.scalar_one_or_none()
    if not obj:
        return False
    await db.delete(obj)
    await db.commit()
    return True


async def list_jobs(
    db: AsyncSession,
    region_id: Optional[uuid.UUID] = None,
    role_id: Optional[uuid.UUID] = None,
    sector_id: Optional[uuid.UUID] = None,
    city: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    is_demo: Optional[bool] = None,
) -> list[JobOut]:
    query = select(JobPosting)
    if region_id:
        query = query.where(JobPosting.region_id == region_id)
    if role_id:
        query = query.where(JobPosting.role_id == role_id)
    if sector_id:
        query = query.where(JobPosting.sector_id == sector_id)
    if city:
        query = query.where(JobPosting.city.ilike(f"%{city}%"))
    if is_demo is not None:
        query = query.where(JobPosting.is_demo == is_demo)
    query = query.order_by(JobPosting.posted_date.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    jobs = result.scalars().all()
    return [_job_to_out(db, j) for j in jobs]


async def get_job(db: AsyncSession, job_id: uuid.UUID) -> JobOut | None:
    result = await db.execute(select(JobPosting).where(JobPosting.id == job_id))
    obj = result.scalar_one_or_none()
    if not obj:
        return None
    return _job_to_out(db, obj)


async def import_jobs_csv(db: AsyncSession, file: UploadFile) -> dict:
    if not file.filename.lower().endswith(".csv"):
        return {"imported": 0, "skipped": 0, "errors": ["Only CSV files are supported"]}
    content = await file.read()
    text = content.decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    imported = 0
    skipped = 0
    errors = []

    async def _resolve_region(city: str, state: str) -> Optional[uuid.UUID]:
        rr = await db.execute(select(Region).where(Region.city.ilike(city), Region.is_active == True))
        region = rr.scalar_one_or_none()
        if not region and state:
            rr = await db.execute(select(Region).where(Region.state.ilike(state), Region.is_active == True))
            region = rr.scalar_one_or_none()
        return region.id if region else None

    async def _resolve_role(title: str) -> Optional[uuid.UUID]:
        # simple keyword matching
        low = title.lower()
        for candidate in ["backend", "frontend", "full stack", "fullstack",
                          "data analyst", "data scientist", "ai/ml", "ai ml",
                          "devops", "cybersecurity", "cloud", "mobile"]:
            if candidate in low:
                rr = await db.execute(select(Role).where(Role.name.ilike(f"%{candidate}%")))
                role = rr.scalar_one_or_none()
                if role:
                    return role.id
        rr = await db.execute(select(Role).where(Role.name.ilike(title), Role.is_active == True))
        role = rr.scalar_one_or_none()
        return role.id if role else None

    async def _resolve_sector(row: dict) -> Optional[uuid.UUID]:
        sector = row.get("sector") or ""
        low = sector.lower()
        for candidate in ["it", "fintech", "finance", "healthcare", "manufacturing", "ecommerce", "saas"]:
            if candidate in low:
                rr = await db.execute(select(Sector).where(Sector.name.ilike(f"%{candidate}%")))
                sec = rr.scalar_one_or_none()
                if sec:
                    return sec.id
        rr = await db.execute(select(Sector).where(Sector.name.ilike(sector), Sector.is_active == True))
        sec = rr.scalar_one_or_none()
        return sec.id if sec else None

    for row in reader:
        try:
            title = (row.get("job_title") or "").strip()
            if not title:
                skipped += 1
                continue
            company = (row.get("company") or "").strip() or None
            city = (row.get("city") or "").strip() or None
            state = (row.get("state") or "").strip() or None
            sector_name = (row.get("sector") or "").strip() or None
            posted = row.get("posted_date") or None
            parsed_date = None
            if posted:
                try:
                    parsed_date = date.fromisoformat(posted)
                except Exception:
                    parsed_date = None
            source = (row.get("source") or "").strip() or None
            source_url = (row.get("source_url") or "").strip() or None
            description = (row.get("description") or "").strip() or None

            region_id = await _resolve_region(city, state)
            role_id = await _resolve_role(title)
            sector_id = await _resolve_sector(row)

            job = JobPosting(
                job_title=title,
                company=company,
                region_id=region_id,
                city=city,
                state=state,
                sector_id=sector_id,
                role_id=role_id,
                description=description,
                posted_date=parsed_date,
                source=source,
                source_url=source_url,
                is_demo=False,
            )
            db.add(job)
            await db.flush()
            await _sync_job_skills(db, job)
            imported += 1
        except Exception as e:
            errors.append(f"Row skipped: {str(e)[:200]}")
            skipped += 1

    await db.commit()
    return {"imported": imported, "skipped": skipped, "errors": errors[:20]}


async def _sync_job_skills(db: AsyncSession, job: JobPosting):
    # clear existing
    for js in list(job.skills):
        await db.delete(js)
    # process required + optional
    seen: dict[uuid.UUID, bool] = {}
    for sname in (job.required_skills or []):
        norm = normalize_skill_name(sname)
        sk = await find_or_create_skill(db, norm)
        if sk:
            js = JobSkill(job_id=job.id, skill_id=sk.id, skill_type="required", confidence=0.95)
            db.add(js)
            seen[sk.id] = True
    for sname in (job.optional_skills or []):
        norm = normalize_skill_name(sname)
        sk = await find_or_create_skill(db, norm)
        if sk:
            js = JobSkill(job_id=job.id, skill_id=sk.id, skill_type="optional", confidence=0.85)
            db.add(js)
            seen[sk.id] = True
    await db.flush()


def _job_to_out(db: AsyncSession, job: JobPosting) -> JobOut:
    return JobOut(
        id=job.id,
        job_title=job.job_title,
        company=job.company,
        region_id=job.region_id,
        city=job.city,
        state=job.state,
        sector_id=job.sector_id,
        role_id=job.role_id,
        description=job.description,
        required_skills=job.required_skills,
        optional_skills=job.optional_skills,
        experience_level=job.experience_level,
        posted_date=job.posted_date,
        source=job.source,
        source_url=job.source_url,
        is_demo=job.is_demo,
        region=job.region,
        role=job.role,
        sector=job.sector,
    )
