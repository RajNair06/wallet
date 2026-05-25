import asyncio
from logging.config import fileConfig
from config import Config
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import pool
from sqlmodel import SQLModel
from alembic import context
from db.models import *

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=Config.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        user_module_prefix="sqlmodel.sql.sqltypes.",  # Forces the generation of SQLModel imports
        render_as_batch=True
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """Synchronous context runner required by Alembic."""
    context.configure(
        connection=connection, 
        target_metadata=target_metadata,
        user_module_prefix="sqlmodel.sql.sqltypes.",  # Forces the generation of SQLModel imports
        render_as_batch=True
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using an async engine."""
    # Use your Config class or fallback to alembic.ini URL
    database_url = getattr(Config, "DATABASE_URL", None) or config.get_main_option("sqlalchemy.url")

    # Create the async engine explicitly
    connectable = create_async_engine(
        database_url,
        poolclass=pool.NullPool,
    )

    async def run_async():
        async with connectable.connect() as connection:
            # run_sync bridges async connection to sync alembic code
            await connection.run_sync(do_run_migrations)

    asyncio.run(run_async())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
