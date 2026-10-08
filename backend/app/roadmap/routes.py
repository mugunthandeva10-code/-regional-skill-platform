import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import User, Project, Roadmap, RoadmapItem
from app.schemas import (
    RoadmapOut, RoadmapItemOut, RoadmapItemUpdate,
    RoadmapGenerateRequest,
)
from app.dependencies import get_current_student
from app.services.roadmap import generate_roadmap, update_roadmap_item, recommend_project_for_skill

router = APIRouter(tags=["roadmap"])


@router.get("/roadmap", response_model=RoadmapOut)
async def get_roadmap(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_student),
):
    result = await db.execute(
        select(Roadmap).where(Roadmap.user_id == user.id)
        .order_by(Roadmap.created_at.desc())
        .limit(1)
    )
    roadmap = result.scalar_one_or_none()
    if not roadmap:
        raise HTTPException(status_code=404, detail="No roadmap yet. Generate one from your profile.")
    items_result = await db.execute(
        select(RoadmapItem)
        .where(RoadmapItem.roadmap_id == roadmap.id)
        .order_by(RoadmapItem.week_number)
    )
    items = items_result.scalars().all()
    out_items = []
    for it in items:
        out_items.append(RoadmapItemOut(
            id=it.id,
            roadmap_id=it.roadmap_id,
            week_number=it.week_number,
            title=it.title,
            skill_id=it.skill_id,
            learning_objective=it.learning_objective,
            recommended_resources=it.recommended_resources,
            practice_task=it.practice_task,
            project_task=it.project_task,
            expected_output=it.expected_output,
            status=it.status,
            learn_status=it.learn_status,
            build_status=it.build_status,
            prove_status=it.prove_status,
            project_id=it.project_id,
            skill=it.skill,
            project=it.project,
        ))
    return RoadmapOut(
        id=roadmap.id,
        user_id=roadmap.user_id,
        target_role_id=roadmap.target_role_id,
        preferred_region_id=roadmap.preferred_region_id,
        title=roadmap.title,
        created_at=roadmap.created_at,
        items=out_items,
    )


@router.post("/roadmap/generate", response_model=RoadmapOut, status_code=201)
async def generate_roadmap_route(
    req: RoadmapGenerateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_student),
):
    if req.user_id != user.id:
        raise HTTPException(status_code=403, detail="Can only generate your own roadmap")
    # Use profile context if set
    from app.models import StudentProfile
    prow = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == user.id)
    )
    profile = prow.scalar_one_or_none()
    region_id = req.region_id or (profile.preferred_region_id if profile else None)
    role_id = req.role_id or (profile.target_role_id if profile else None)
    sector_id = profile.target_sector_id if profile else None
    return await generate_roadmap(
        db, user, region_id, role_id, sector_id,
        weeks=req.weeks,
    )


@router.put("/roadmap/items/{item_id}", response_model=RoadmapItemOut)
async def update_roadmap_item_route(
    item_id: uuid.UUID,
    update: RoadmapItemUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_student),
):
    try:
        return await update_roadmap_item(db, item_id, user.id, update)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/roadmap/{skill_name}/project-recommendation")
async def project_recommendation_route(
    skill_name: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_student),
):
    rec = await recommend_project_for_skill(db, skill_name)
    return rec
