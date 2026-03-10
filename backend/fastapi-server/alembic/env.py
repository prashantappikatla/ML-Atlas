import os
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

# Import all models so Alembic sees them for autogenerate
from app.models.algorithm import Algorithm, AlgorithmParameter, AlgorithmNote  # noqa: F401
from app.models.lab import Lab  # noqa: F401
from app.models.status import ImplementationStatus  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Load environment variables from .env files (backend and repo root)
BACKEND_PATH = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_PATH.parent.parent
BACKEND_ENV = BACKEND_PATH / ".env"
ROOT_ENV = REPO_ROOT / ".env"

if BACKEND_ENV.exists():
    load_dotenv(BACKEND_ENV, override=False)
if ROOT_ENV.exists():
    load_dotenv(ROOT_ENV, override=False)

# Override sqlalchemy.url with DATABASE_URL env var
database_url = os.environ.get("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
