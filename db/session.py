from sqlmodel import  SQLModel
from sqlalchemy.ext.asyncio import create_async_engine
from typing import AsyncGenerator
from sqlmodel.ext.asyncio.session import AsyncSession
from config import Config

engine = create_async_engine(Config.DATABASE_URL)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(engine) as session:
        yield session