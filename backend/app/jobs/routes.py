import uuid
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import User, JobPosting
from app.schemas import (
    JobOut, JobCreate, JobUpdate, JobListQuery,
)
from app.dependencies import get_current_user, get_current_admin
from app.services.jobs import (
    create_job, update_job, delete_job, list_jobs, get_job, import_jobs_csv,
)
from app.services.seed import seed_demo_data

router = APIRouter(tags=["jobs"])


@router.get("/jobs", response_model=list[JobOut])
async def get_jobs(
    region_id: Optional[uuid.UUID] = None,
    role_id: Optional[uuid.UUID] = None,
    sector_id: Optional[uuid.UUID] = None,
    city: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    is_demo: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await list_jobs(db, region_id, role_id, sector_id, city, limit, offset, is_demo)


@router.get("/jobs/{job_id}", response_model=JobOut)
async def get_job_route(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    job = await get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/jobs", response_model=JobOut, status_code=status.HTTP_201_CREATED)
async def create_job_route(
    data: JobCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    return await create_job(db, data, is_demo=False)


@router.put("/jobs/{job_id}", response_model=JobOut)
async def update_job_route(
    job_id: uuid.UUID,
    data: JobUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    try:
        return await update_job(db, job_id, data)
    except ValueError:
        raise HTTPException(status_code=404, detail="Job not found")


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job_route(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    ok = await delete_job(db, job_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Job not found")


@router.post("/admin/import-jobs", status_code=status.HTTP_200_OK)
async def import_jobs_route(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    result = await import_jobs_csv(db, file)
    return result


@router.post("/admin/seed-demo", status_code=status.HTTP_200_OK)
async def seed_demo_route(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_admin),
):
    counts = await seed_demo_data(db, force=True)
    return counts
