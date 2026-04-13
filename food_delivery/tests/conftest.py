import os
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from fakeredis.aioredis import FakeRedis
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "123456:ABCDEF-test-token-for-tests-min-length")
os.environ.setdefault("SECRET_KEY", "x" * 32)
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("BACKEND_URL", "http://test")
os.environ.setdefault("WEBAPP_URL", "http://test/webapp")

from app.main import app
from app.models import Base
from app.models.user import User


@pytest_asyncio.fixture
async def engine():
    eng = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def async_db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    Session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with Session() as session:
        yield session


@pytest.fixture
def redis_mock() -> FakeRedis:
    return FakeRedis(decode_responses=False)


@pytest_asyncio.fixture
async def test_user(async_db_session: AsyncSession) -> User:
    u = User(telegram_id=999001, first_name="Test", language="uz", is_admin=False)
    async_db_session.add(u)
    await async_db_session.commit()
    await async_db_session.refresh(u)
    return u


@pytest_asyncio.fixture
async def test_client(engine, redis_mock: FakeRedis) -> AsyncGenerator[AsyncClient, None]:
    Session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with Session() as session:
            yield session

    from app.db.session import get_db

    app.dependency_overrides[get_db] = override_get_db
    app.state.redis = redis_mock

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_headers(test_client: AsyncClient, test_user: User) -> dict[str, str]:
    from app.core.security import create_access_token

    token = create_access_token(user_id=test_user.id, telegram_id=test_user.telegram_id)
    return {"Authorization": f"Bearer {token}"}
