from datetime import timedelta
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import User
from app.schemas import (
    RegisterRequest, LoginRequest, TokenResponse, UserOut, UserUpdate,
)
from app.dependencies import get_current_user
from app.auth.hash import hash_password, verify_password
from app.auth.jwt import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == req.email.lower()))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=req.email.lower(),
        hashed_password=hash_password(req.password),
        full_name=req.full_name,
        role="student",
        college=req.college,
        department=req.department,
        degree=req.degree,
        graduation_year=req.graduation_year,
        location=req.location,
        target_role_id=req.target_role_id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role},
        expires_delta=timedelta(minutes=1440),
    )
    return TokenResponse(
        access_token=access_token,
        user=UserOut.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == req.email.lower()))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role},
    )
    return TokenResponse(
        access_token=access_token,
        user=UserOut.model_validate(user),
    )


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return UserOut.model_validate(user)


@router.put("/me", response_model=UserOut)
async def update_me(
    update: UserUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if update.role is not None and update.role not in ("student", "admin"):
        raise HTTPException(status_code=400, detail="role must be student or admin")

    if update.email is not None:
        conflict = await db.execute(
            select(User).where(User.email == update.email.lower(), User.id != user.id)
        )
        if conflict.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already registered")
        user.email = update.email.lower()

    if update.password is not None:
        user.hashed_password = hash_password(update.password)

    for field, value in update.model_dump(exclude_unset=True, exclude={"email", "password"}).items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    return UserOut.model_validate(user)
