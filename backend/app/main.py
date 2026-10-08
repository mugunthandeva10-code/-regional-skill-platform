from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base, async_session_maker
from app.config import get_settings
from app.services.seed import seed_demo_data
from app.auth.routes import router as auth_router
from app.students.routes import router as students_router, projects_router
from app.skills.routes import router as skills_router
from app.jobs.routes import router as jobs_router
from app.demand.routes import router as demand_router
from app.gaps.routes import router as gaps_router
from app.roadmap.routes import router as roadmap_router
from app.admin.routes import router as admin_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables (for MVP; use alembic in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Auto-seed demo data if enabled
    if settings.demo_auto_seed:
        async with async_session_maker() as session:
            await seed_demo_data(session, force=True)
    yield
    # shutdown


app = FastAPI(
    title="Regional Skill Intelligence Platform API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # configure per environment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(students_router)
app.include_router(projects_router)
app.include_router(skills_router)
app.include_router(jobs_router)
app.include_router(demand_router)
app.include_router(gaps_router)
app.include_router(roadmap_router)
app.include_router(admin_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "skill-intelligence-api"}
