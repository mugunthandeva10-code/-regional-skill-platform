import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import (
    User, Skill, SkillAlias, Region, Role, Sector,
)
from app.schemas import (
    SkillOut, SkillCreate, SkillAliasOut,
    RegionOut, RegionCreate,
    RoleOut, RoleCreate,
    SectorOut, SectorCreate,
)
from app.dependencies import get_current_user, get_current_admin

router = APIRouter(tags=["skills-taxonomy"])


# ---------------- Skills ----------------

@router.get("/skills", response_model=list[SkillOut])
async def list_skills(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Skill).where(Skill.is_active == True).order_by(Skill.name))
    rows = result.scalars().all()
    return [SkillOut.model_validate(r) for r in rows]


@router.post("/skills", response_model=SkillOut, status_code=status.HTTP_201_CREATED)
async def create_skill(
    data: SkillCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    existing = await db.execute(select(Skill).where(Skill.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Skill already exists")
    obj = Skill(**data.model_dump())
    db.add(obj)
    await db.flush()
    for alias in data.aliases:
        db.add(SkillAlias(skill_id=obj.id, alias=alias))
    await db.commit()
    await db.refresh(obj)
    return SkillOut.model_validate(obj)


@router.put("/skills/{skill_id}", response_model=SkillOut)
async def update_skill(
    skill_id: uuid.UUID,
    data: SkillCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Skill not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    await db.flush()
    # sync aliases
    await db.execute(SkillAlias.__table__.delete().where(SkillAlias.skill_id == skill_id))
    for alias in data.aliases:
        db.add(SkillAlias(skill_id=skill_id, alias=alias))
    await db.commit()
    await db.refresh(obj)
    return SkillOut.model_validate(obj)


@router.delete("/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    skill_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Skill not found")
    obj.is_active = False
    await db.commit()


@router.get("/skills/{skill_id}/aliases", response_model=list[SkillAliasOut])
async def list_aliases(
    skill_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(SkillAlias).where(SkillAlias.skill_id == skill_id))
    rows = result.scalars().all()
    return [SkillAliasOut.model_validate(r) for r in rows]


# ---------------- Regions ----------------

@router.get("/regions", response_model=list[RegionOut])
async def list_regions(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Region).where(Region.is_active == True).order_by(Region.name))
    rows = result.scalars().all()
    return [RegionOut.model_validate(r) for r in rows]


@router.post("/regions", response_model=RegionOut, status_code=status.HTTP_201_CREATED)
async def create_region(
    data: RegionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    existing = await db.execute(select(Region).where(Region.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Region already exists")
    obj = Region(**data.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return RegionOut.model_validate(obj)


@router.put("/regions/{region_id}", response_model=RegionOut)
async def update_region(
    region_id: uuid.UUID,
    data: RegionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    result = await db.execute(select(Region).where(Region.id == region_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Region not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return RegionOut.model_validate(obj)


# ---------------- Roles ----------------

@router.get("/roles", response_model=list[RoleOut])
async def list_roles(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Role).where(Role.is_active == True).order_by(Role.name))
    rows = result.scalars().all()
    return [RoleOut.model_validate(r) for r in rows]


@router.post("/roles", response_model=RoleOut, status_code=status.HTTP_201_CREATED)
async def create_role(
    data: RoleCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    existing = await db.execute(select(Role).where(Role.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Role already exists")
    obj = Role(**data.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return RoleOut.model_validate(obj)


@router.put("/roles/{role_id}", response_model=RoleOut)
async def update_role(
    role_id: uuid.UUID,
    data: RoleCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    result = await db.execute(select(Role).where(Role.id == role_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Role not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return RoleOut.model_validate(obj)


# ---------------- Sectors ----------------

@router.get("/sectors", response_model=list[SectorOut])
async def list_sectors(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Sector).where(Sector.is_active == True).order_by(Sector.name))
    rows = result.scalars().all()
    return [SectorOut.model_validate(r) for r in rows]


@router.post("/sectors", response_model=SectorOut, status_code=status.HTTP_201_CREATED)
async def create_sector(
    data: SectorCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    existing = await db.execute(select(Sector).where(Sector.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Sector already exists")
    obj = Sector(**data.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return SectorOut.model_validate(obj)


@router.put("/sectors/{sector_id}", response_model=SectorOut)
async def update_sector(
    sector_id: uuid.UUID,
    data: SectorCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    result = await db.execute(select(Sector).where(Sector.id == sector_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Sector not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return SectorOut.model_validate(obj)
