"""
Test fixtures for the Sightline API test suite.

The `client` fixture provides an httpx AsyncClient wired to the FastAPI app
with the database dependency overridden. Each test runs inside a transaction
that is rolled back on teardown — no data is ever committed to the database.
"""

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import settings
from app.db.session import get_db
from app.main import app

# Separate engine for tests — NullPool so connections are not reused between tests.
_test_engine = create_async_engine(settings.database_url, poolclass=NullPool)


@pytest_asyncio.fixture()
async def client():
    """
    AsyncClient with a per-test database session that rolls back after the test.

    The override replaces the app's get_db dependency with a session bound to
    an open transaction. When the fixture tears down, the transaction is rolled
    back rather than committed, leaving the database unchanged.
    """
    async with _test_engine.connect() as conn:
        await conn.begin()

        # Bind a session to this connection so all operations share the same
        # transaction and can be rolled back together.
        session = AsyncSession(bind=conn, expire_on_commit=False)

        async def override_get_db():
            yield session

        app.dependency_overrides[get_db] = override_get_db

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            yield ac

        await session.close()
        await conn.rollback()

    app.dependency_overrides.clear()
