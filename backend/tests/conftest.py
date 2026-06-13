import asyncio
import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import UUID, JSONB

@compiles(UUID, "sqlite")
def compile_uuid_sqlite(element, compiler, **kw):
    return "VARCHAR(36)"

@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(element, compiler, **kw):
    return "JSON"

# Import FastAPI app and settings
from app.main import app
from app.core.config import settings
from app.core.database import get_db
from app.db.base import Base

# Override database URL for local test execution outside Docker container
db_url = settings.DATABASE_URL
if "db:5432" in db_url and not os.path.exists("/.dockerenv"):
    db_url = "sqlite+aiosqlite:///:memory:"

# Create a test database engine
if "sqlite" in db_url:
    from sqlalchemy.pool import StaticPool
    test_engine = create_async_engine(db_url, poolclass=StaticPool, future=True)
else:
    test_engine = create_async_engine(db_url, future=True)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create a session-wide event loop for running async fixtures."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def init_db():
    """Automatically create all tables at start and drop them at the end of the test session."""
    from sqlalchemy import text
    async with test_engine.begin() as conn:
        if test_engine.dialect.name != "sqlite":
            # Enable uuid-ossp and vector extensions on the test database
            await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
            await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "vector"'))
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional database session rolled back at test completion."""
    async with test_engine.connect() as connection:
        transaction = await connection.begin()
        session = TestingSessionLocal(bind=connection)

        yield session

        await session.close()
        await transaction.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """FastAPI AsyncClient overriding database sessions to use the transactional fixture."""
    async def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()