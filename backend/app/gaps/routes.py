import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import User
from app.schemas import (
    SkillGapOut, SkillGapList, SkillGapAnalyzeRequest,
)
from app.dependencies import get_current_student
from app.services.gaps import analyze_skill_gaps

router = APIRouter(tags=["skill-gaps"])


@router.get("/skill-gap", response_model=SkillGapList)
async def get_skill_gaps(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_student),
):
    profile_result = await db.execute(
        select(User).where(User.id == user.id)
    )
    # Use profile context if set
    from app.models import StudentProfile
    prow = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == user.id)
    )
    profile = prow.scalar_one_or_none()
    region_id = profile.preferred_region_id if profile else None
    role_id = profile.target_role_id if profile else None
    sector_id = profile.target_sector_id if profile else None
    return await analyze_skill_gaps(db, user, region_id, role_id, sector_id)


@router.post("/skill-gap/analyze", response_model=SkillGapList)
async def analyze_gaps(
    req: SkillGapAnalyzeRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_student),
):
    if req.user_id != user.id:
        raise HTTPException(status_code=403, detail="Can only analyze your own gaps")
    return await analyze_skill_gaps(
        db, user,
        req.region_id, req.role_id, req.sector_id,
        req.time_window,
    )
