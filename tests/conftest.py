import os
from typing import AsyncGenerator
from unittest.mock import patch

import fakeredis.aioredis
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

os.environ["SECRET_KEY"] = "test-secret-key-1234567890"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["BREVO_API_KEY"] = "test-key"
os.environ["SENDER_MAIL"] = "test@example.com"
os.environ["SENDER_NAME"] = "Test"

import db.session

db.session.engine = create_async_engine("sqlite+aiosqlite://", echo=False)

import middleware.idempotency

middleware.idempotency.redis = fakeredis.aioredis.FakeRedis()

from main import app as _app
from core.limiter import (auth_limiter, deposit_limiter, sensitive_txn_limiter,
                          signup_limiter)
from core.security import create_access_token, hash_password
from db.models import EntryType, LedgerEntry, Transaction, TransactionType, User, Wallet

_app.dependency_overrides[signup_limiter] = lambda: None
_app.dependency_overrides[auth_limiter] = lambda: None
_app.dependency_overrides[sensitive_txn_limiter] = lambda: None
_app.dependency_overrides[deposit_limiter] = lambda: None


@pytest.fixture(autouse=True)
def _mock_worker():
    with patch("workers.mail_reciept.send") as mock:
        yield mock


@pytest.fixture(autouse=True)
def _fresh_redis():
    middleware.idempotency.redis = fakeredis.aioredis.FakeRedis()
    yield


@pytest_asyncio.fixture(autouse=True)
async def _setup_db():
    async with db.session.engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with db.session.engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def session():
    async with db.session.AsyncSession(db.session.engine, expire_on_commit=False) as s:
        yield s


@pytest_asyncio.fixture
async def test_user(session) -> User:
    user = User(
        first_name="Test",
        last_name="User",
        email="test@example.com",
        hashed_password=hash_password("testpassword123"),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_user2(session) -> User:
    user = User(
        first_name="Test2",
        last_name="User2",
        email="test2@example.com",
        hashed_password=hash_password("testpassword123"),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_token(client, test_user) -> str:
    response = await client.post(
        "/token",
        data={"username": "test@example.com", "password": "testpassword123"},
    )
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def auth_token2(client, test_user2) -> str:
    response = await client.post(
        "/token",
        data={"username": "test2@example.com", "password": "testpassword123"},
    )
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def wallet(session, test_user) -> Wallet:
    w = Wallet(user_id=test_user.id, balance=10000, currency="USD")
    session.add(w)
    await session.commit()
    await session.refresh(w)
    return w


@pytest_asyncio.fixture
async def wallet2(session, test_user2) -> Wallet:
    w = Wallet(user_id=test_user2.id, balance=5000, currency="USD")
    session.add(w)
    await session.commit()
    await session.refresh(w)
    return w
