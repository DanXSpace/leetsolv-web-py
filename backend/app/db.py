"""Database engine, session factory, and declarative base."""

from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.environ.get("LEETSOLV_DATABASE_URL", "sqlite:///./leetsolv.db")


class Base(DeclarativeBase):
    pass


def _engine_for(url: str):
    kwargs: dict = {}
    if url.startswith("sqlite"):
        # Allow the engine to be shared across FastAPI's thread pool.
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **kwargs)


engine = _engine_for(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    """Create all tables. Imports models so they register with Base first."""
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
