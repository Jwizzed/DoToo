import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine
from sqlalchemy import pool

project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_dir)

from app.core.config import settings
from app.db.base import Base
from app.db import models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """

    url = settings.DATABASE_URL
    print(f"Running migrations offline with URL: {url}")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    This function uses a SYNCHRONOUS engine connection
    derived from the application's async database URL.
    """

    async_db_url = settings.DATABASE_URL
    if not async_db_url:
        raise ValueError("DATABASE_URL is not set in the configuration.")

    try:
        if "+asyncpg" in async_db_url:
            sync_db_url = async_db_url.replace("+asyncpg", "+psycopg2")
        elif async_db_url.startswith("postgresql://"):
            sync_db_url = async_db_url
        else:
            print(
                f"Warning: Unrecognized DATABASE_URL scheme for sync conversion: {async_db_url}. Attempting direct use."
            )
            sync_db_url = async_db_url

    except Exception as e:
        raise ValueError(
            f"Error processing DATABASE_URL for synchronous connection: {e}"
        )

    print(f"Alembic running migrations online using SYNC URL: {sync_db_url}")

    connectable = create_engine(sync_db_url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
