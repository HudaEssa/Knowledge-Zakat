"""
Knowledge Zakat — Database connection
=====================================
Switched from raw SQLAlchemy `declarative_base()` to `SQLModel.metadata`,
which is the canonical way to wire SQLModel models to the schema.

Security improvement: the database URL is now read from the environment
(via `.env`) instead of being hard-coded. The previous version had the
production-style password baked into the source file, which is a leak
waiting to happen the moment the repo is pushed anywhere.
"""

from sqlmodel import SQLModel, create_engine, Session

from core.config import settings


# `pool_pre_ping=True` is cheap insurance against stale connections in
# development (postgres restarts, laptop sleep, etc.). `echo` is off in
# production but configurable from the env if you want SQL traces.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.SQL_ECHO,
)


def init_db() -> None:
    """
    Create all tables for SQLModel-registered models.
    Called once from main.py on startup. In a production setup this
    would be replaced by Alembic migrations, but for the graduation
    project create_all is fine.
    """
    SQLModel.metadata.create_all(engine)


def get_db():
    """
    FastAPI dependency. Yields a SQLModel `Session` and guarantees it
    is closed even if the request raises. Type-hint your routes with
    `Session = Depends(get_db)` (SQLModel's Session, not SQLAlchemy's).
    """
    with Session(engine) as session:
        yield session


# Backwards-compatibility shim ------------------------------------------------
# The previous code did `models.Base.metadata.create_all(bind=engine)`.
# We expose `Base` as an alias so any leftover import does not break;
# new code should call `init_db()` instead.
Base = SQLModel
