import os
import sys
from logging.config import fileConfig
from sqlalchemy.ext.asyncio import create_async_engine # Change import
from sqlalchemy import pool
from alembic import context

# Load .env file - ADD THIS SECTION
from dotenv import load_dotenv
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

# Ensure the 'app' directory is in the Python path - ADD THIS
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

# Import Base and settings - MODIFY THIS SECTION
from app.db.base import Base # Import your Base
# from app.core.config import settings # Or directly get DATABASE_URL if simpler

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata # SET YOUR BASE METADATA HERE

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

# Get DATABASE_URL from environment variable loaded by dotenv - ADD THIS
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set or .env file not found")

# Update the sqlalchemy.url in the config object - ADD THIS
config.set_main_option('sqlalchemy.url', DATABASE_URL)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# MODIFY THIS FUNCTION FOR ASYNC
def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = create_async_engine( # Use create_async_engine
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection: # Use async context manager
        await connection.run_sync(do_run_migrations) # Run sync function within async context

    await connectable.dispose() # Dispose async engine


if context.is_offline_mode():
    run_migrations_offline()
else:
    # Run the async function using asyncio.run
    import asyncio
    asyncio.run(run_migrations_online()) # Use asyncio.run
