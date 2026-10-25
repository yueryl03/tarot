"""Pytest fixtures.

Integration tests use ``TAROT_TEST_DATABASE_URL`` when set, otherwise a local
``tarot_test`` database. The database name must contain ``test``.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

BACKEND_ROOT = Path(__file__).resolve().parents[1]
TEST_DATABASE_URL = os.environ.get(
    "TAROT_TEST_DATABASE_URL",
    "postgresql+asyncpg://tarot:tarot@localhost:5432/tarot_test",
)
DATABASE_NAME = TEST_DATABASE_URL.rsplit("/", 1)[-1].split("?", 1)[0]

if not re.fullmatch(r"[A-Za-z0-9_]+", DATABASE_NAME) or "test" not in DATABASE_NAME:
    raise RuntimeError(f"Refusing to use non-test database '{DATABASE_NAME}'")

os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ.setdefault("INTERPRETATION_PROVIDER", "mock")
os.environ["INTERPRETATION_API_KEY"] = ""

TRUNCATE_SQL = """
TRUNCATE TABLE
    interpretations,
    idempotency_keys,
    reading_draws,
    reading_deck_slots,
    reading_sessions
RESTART IDENTITY CASCADE
"""


def _asyncpg_dsn(url: str) -> str:
    return url.replace("postgresql+asyncpg://", "postgresql://", 1)


async def _ensure_database() -> bool:
    import asyncpg

    target = _asyncpg_dsn(TEST_DATABASE_URL)
    try:
        connection = await asyncpg.connect(target, timeout=3)
    except Exception:
        admin = _asyncpg_dsn(TEST_DATABASE_URL.rsplit("/", 1)[0] + "/postgres")
        try:
            connection = await asyncpg.connect(admin, timeout=3)
        except Exception:
            return False
        exists = await connection.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            DATABASE_NAME,
        )
        if not exists:
            await connection.execute(f'CREATE DATABASE "{DATABASE_NAME}"')
        await connection.close()
        try:
            connection = await asyncpg.connect(target, timeout=3)
        except Exception:
            return False
    await connection.close()
    return True


def _migrate() -> None:
    env = os.environ.copy()
    env["DATABASE_URL"] = TEST_DATABASE_URL
    env["PYTHONPATH"] = str(BACKEND_ROOT)
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND_ROOT,
        env=env,
        check=True,
    )


@pytest.fixture(scope="session")
async def engine() -> AsyncIterator[AsyncEngine]:
    if not await _ensure_database():
        pytest.skip("PostgreSQL is not available for integration tests")
    _migrate()
    from app.core.config import get_settings
    from app.db.seed import seed_database

    get_settings.cache_clear()
    eng = create_async_engine(
        TEST_DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )
    factory = async_sessionmaker(eng, expire_on_commit=False)
    async with factory() as session:
        await seed_database(session)
        await session.commit()
    yield eng
    await eng.dispose()


@pytest.fixture
async def database(engine: AsyncEngine) -> AsyncIterator[AsyncEngine]:
    async with engine.begin() as connection:
        await connection.execute(text(TRUNCATE_SQL))
    yield engine


@pytest.fixture
async def session_factory(database: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(database, expire_on_commit=False)


@pytest.fixture
async def client(database: AsyncEngine):
    from httpx import ASGITransport, AsyncClient

    from app.db.session import get_db
    from app.main import create_app

    application = create_app()
    factory = async_sessionmaker(database, expire_on_commit=False)

    async def override_db() -> AsyncIterator[AsyncSession]:
        async with factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    application.dependency_overrides[get_db] = override_db
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as http:
        yield http
    application.dependency_overrides.clear()
