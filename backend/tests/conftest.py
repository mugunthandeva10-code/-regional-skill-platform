import os

# Use a portable SQLite database for tests so they do not require a running PostgreSQL.
# Must be set before importing the app (settings are read at import time).
TEST_DB_FILE = "./test_skill_platform.db"
os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{TEST_DB_FILE}")
os.environ["DEMO_AUTO_SEED"] = "false"

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import async_session_maker, engine, Base
from app.services.seed import seed_demo_data


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(scope="session")
async def db():
    # Fresh database per test session.
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except OSError:
            pass
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session_maker() as session:
        await seed_demo_data(session, force=True)
        yield session
        await session.close()


@pytest_asyncio.fixture
async def client(db):
    app.dependency_overrides.clear()
    from app.database import get_db

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
