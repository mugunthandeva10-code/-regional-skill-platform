import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import (
    User, StudentProfile, Resume, StudentSkill, Skill, SkillAlias,
    Project, Region, Role, Sector,
)
from app.schemas import (
    ProfileCreate, ProfileOut, ResumeUploadResponse, SkillExtractOut,
    StudentSkillIn, StudentSkillOut, SkillOut,
    RegionOut, RoleOut, SectorOut,
    ProjectCreate, ProjectUpdate, ProjectOut,
)
from app.dependencies import get_current_student
from app.auth.jwt import decode_access_token
from app.services.resume_parser import extract_text_from_pdf, extract_skills_from_text
from app.services.skill_matcher import normalize_skill_name, find_or_create_skill
from app.services.demand import build_demand_context

router = APIRouter(prefix="/students", tags=["students"])


@router.get("/profile", response_model=ProfileOut)
async def get_profile(user: User = Depends(get_current_student), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found. Complete onboarding first.")
    return ProfileOut(
        id=profile.id,
        user_id=profile.user_id,
        target_role_id=profile.target_role_id,
        target_sector_id=profile.target_sector_id,
        preferred_region_id=profile.preferred_region_id,
        summary=profile.summary,
        target_role=profile.target_role,
        target_sector=profile.target_sector,
        preferred_region=profile.preferred_region,
    )


@router.put("/profile", response_model=ProfileOut)
async def update_profile(
    profile: ProfileCreate,
    user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == user.id))
    existing = result.scalar_one_or_none()
    if existing:
        existing.target_role_id = profile.target_role_id
        existing.target_sector_id = profile.target_sector_id
        existing.preferred_region_id = profile.preferred_region_id
        existing.summary = profile.summary
        profile_obj = existing
    else:
        profile_obj = StudentProfile(
            user_id=user.id,
            target_role_id=profile.target_role_id,
            target_sector_id=profile.target_sector_id,
            preferred_region_id=profile.preferred_region_id,
            summary=profile.summary,
        )
        db.add(profile_obj)

    await db.commit()
    await db.refresh(profile_obj)

    result2 = await db.execute(select(StudentProfile).where(StudentProfile.id == profile_obj.id))
    refreshed = result2.scalar_one()
    return ProfileOut(
        id=refreshed.id,
        user_id=refreshed.user_id,
        target_role_id=refreshed.target_role_id,
        target_sector_id=refreshed.target_sector_id,
        preferred_region_id=refreshed.preferred_region_id,
        summary=refreshed.summary,
        target_role=refreshed.target_role,
        target_sector=refreshed.target_sector,
        preferred_region=refreshed.preferred_region,
    )


@router.post("/resume", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")

    import os, uuid as _uuid
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    storage_name = f"{_uuid.uuid4().hex}_{file.filename}"
    storage_path = os.path.join(upload_dir, storage_name)
    with open(storage_path, "wb") as f:
        f.write(content)

    extracted_text = extract_text_from_pdf(storage_path)
    if not extracted_text:
        raise HTTPException(status_code=400, detail="Could not extract text from PDF")

    raw_skills = extract_skills_from_text(extracted_text)
    normalized = []
    for s in raw_skills:
        norm = normalize_skill_name(s.get("name", ""))
        matched = await find_or_create_skill(db, norm)
        normalized.append(SkillExtractOut(
            name=s.get("name", ""),
            normalized=matched.name if matched else norm,
            confidence=float(s.get("confidence", 0.0)),
            status="matched" if matched else "unrecognized",
        ))

    # Upsert profile if missing
    res = await db.execute(select(StudentProfile).where(StudentProfile.user_id == user.id))
    profile_row = res.scalar_one_or_none()
    if not profile_row:
        profile_row = StudentProfile(user_id=user.id)
        db.add(profile_row)
        await db.flush()

    existing_resume = await db.execute(
        select(Resume).where(Resume.user_id == user.id)
    )
    resume_obj = existing_resume.scalar_one_or_none()
    if resume_obj:
        resume_obj.original_filename = file.filename
        resume_obj.storage_path = storage_path
        resume_obj.extracted_text = extracted_text
        resume_obj.extracted_skills = [
            {"name": n.name, "normalized": n.normalized, "confidence": n.confidence}
            for n in normalized
        ]
        resume_obj.parsed_at = None
    else:
        resume_obj = Resume(
            user_id=user.id,
            original_filename=file.filename,
            storage_path=storage_path,
            extracted_text=extracted_text,
            extracted_skills=[
                {"name": n.name, "normalized": n.normalized, "confidence": n.confidence}
                for n in normalized
            ],
        )
        db.add(resume_obj)

    await db.commit()
    await db.refresh(resume_obj)

    return ResumeUploadResponse(
        id=resume_obj.id,
        original_filename=resume_obj.original_filename,
        extracted_skills=normalized,
        message="Resume processed. Review and confirm extracted skills.",
    )


@router.get("/skills", response_model=list[StudentSkillOut])
async def get_skills(
    user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(StudentSkill)
        .where(StudentSkill.user_id == user.id)
        .order_by(StudentSkill.skill_id)
    )
    rows = result.scalars().all()
    out = []
    for r in rows:
        out.append(StudentSkillOut(
            id=r.id,
            user_id=r.user_id,
            skill_id=r.skill_id,
            level=r.level,
            source=r.source,
            confidence=r.confidence,
            is_confirmed=r.is_confirmed,
            skill=r.skill,
        ))
    return out


@router.put("/skills", response_model=list[StudentSkillOut])
async def upsert_skills(
    skills: list[StudentSkillIn],
    user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    out = []
    for in_s in skills:
        result = await db.execute(
            select(StudentSkill).where(
                and_(
                    StudentSkill.user_id == user.id,
                    StudentSkill.skill_id == in_s.skill_id,
                )
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.level = in_s.level
            existing.confidence = in_s.confidence
            existing.is_confirmed = in_s.is_confirmed
            obj = existing
        else:
            obj = StudentSkill(
                user_id=user.id,
                skill_id=in_s.skill_id,
                level=in_s.level,
                source=in_s.source,
                confidence=in_s.confidence,
                is_confirmed=in_s.is_confirmed,
            )
            db.add(obj)
        await db.flush()
        await db.refresh(obj, ["skill"])
        out.append(StudentSkillOut(
            id=obj.id,
            user_id=obj.user_id,
            skill_id=obj.skill_id,
            level=obj.level,
            source=obj.source,
            confidence=obj.confidence,
            is_confirmed=obj.is_confirmed,
            skill=obj.skill,
        ))
    await db.commit()
    return out


@router.delete("/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_skill(
    skill_id: uuid.UUID,
    user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(StudentSkill).where(
            and_(StudentSkill.user_id == user.id, StudentSkill.skill_id == skill_id)
        )
    )
    row = result.scalar_one_or_none()
    if row:
        await db.delete(row)
        await db.commit()


@router.get("/options")
async def get_options(
    user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    regions = await db.execute(select(Region).where(Region.is_active == True).order_by(Region.name))
    roles = await db.execute(select(Role).where(Role.is_active == True).order_by(Role.name))
    sectors = await db.execute(select(Sector).where(Sector.is_active == True).order_by(Sector.name))
    skills = await db.execute(select(Skill).where(Skill.is_active == True).order_by(Skill.name))
    return {
        "regions": [RegionOut.model_validate(r) for r in regions.scalars().all()],
        "roles": [RoleOut.model_validate(r) for r in roles.scalars().all()],
        "sectors": [SectorOut.model_validate(r) for r in sectors.scalars().all()],
        "skills": [SkillOut.model_validate(s) for s in skills.scalars().all()],
    }


@router.post("/projects", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    project: ProjectCreate,
    user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    obj = Project(**project.model_dump(), user_id=user.id)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return ProjectOut.model_validate(obj)


# --- Top-level /projects aliases (spec API surface) ---
# Reuses the same student-scoped handlers, mounted without the /students prefix.
projects_router = APIRouter(prefix="/projects", tags=["projects"])


@projects_router.get("", response_model=list[ProjectOut])
async def list_projects_root(
    user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    return await _list_projects_impl(user, db)


@projects_router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project_root(
    project: ProjectCreate,
    user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    return await _create_project_impl(project, user, db)


@projects_router.put("/{project_id}", response_model=ProjectOut)
async def update_project_root(
    project_id: uuid.UUID,
    update: ProjectUpdate,
    user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    return await _update_project_impl(project_id, update, user, db)


# --- Internals used by both /students/projects and /projects ---
async def _list_projects_impl(user: User, db: AsyncSession) -> list[ProjectOut]:
    result = await db.execute(
        select(Project)
        .where(Project.user_id == user.id)
        .order_by(Project.created_at.desc())
    )
    return [ProjectOut.model_validate(r) for r in result.scalars().all()]


async def _create_project_impl(
    project: ProjectCreate, user: User, db: AsyncSession
) -> ProjectOut:
    obj = Project(**project.model_dump(), user_id=user.id)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return ProjectOut.model_validate(obj)


async def _update_project_impl(
    project_id: uuid.UUID,
    update: ProjectUpdate,
    user: User,
    db: AsyncSession,
) -> ProjectOut:
    result = await db.execute(select(Project).where(Project.id == project_id))
    obj = result.scalar_one_or_none()
    if not obj or obj.user_id != user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    for k, v in update.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return ProjectOut.model_validate(obj)


@router.get("/projects", response_model=list[ProjectOut])
async def list_projects(
    user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Project)
        .where(Project.user_id == user.id)
        .order_by(Project.created_at.desc())
    )
    rows = result.scalars().all()
    return [ProjectOut.model_validate(r) for r in rows]


@router.put("/projects/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: uuid.UUID,
    update: ProjectUpdate,
    user: User = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    obj = result.scalar_one_or_none()
    if not obj or obj.user_id != user.id:
        raise HTTPException(status_code=404, detail="Project not found")
    data = update.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return ProjectOut.model_validate(obj)
