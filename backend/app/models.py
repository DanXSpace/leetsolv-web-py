"""SQLAlchemy ORM models for leetsolv-web.

The `Problem` model mirrors leetsolv's `core.Question` fields exactly
(url, note, familiarity, importance, last_reviewed, next_review, review_count,
ease_factor) and adds the LeetCode metadata (title/difficulty/tags) that a
mentor view needs.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import CheckConstraint, Date, DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Problem(Base):
    __tablename__ = "problems"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    url: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String, index=True, nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    familiarity: Mapped[int] = mapped_column(Integer, nullable=False)  # 0..4 (VeryHard..VeryEasy)
    importance: Mapped[int] = mapped_column(Integer, nullable=False)  # 0..3 (Low..Critical)
    last_reviewed: Mapped[date] = mapped_column(Date, nullable=False)
    next_review: Mapped[date] = mapped_column(Date, nullable=False)
    review_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ease_factor: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Enriched LeetCode metadata (nullable until resolved from the dataset)
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    difficulty: Mapped[str | None] = mapped_column(String, nullable=True)  # Easy/Medium/Hard
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    __table_args__ = (
        CheckConstraint("familiarity >= 0 AND familiarity <= 4", name="ck_problem_familiarity"),
        CheckConstraint("importance >= 0 AND importance <= 3", name="ck_problem_importance"),
        CheckConstraint("review_count >= 0", name="ck_problem_review_count"),
        CheckConstraint("ease_factor >= 1.0 AND ease_factor <= 3.0", name="ck_problem_ease_factor"),
    )

    def to_state_dict(self) -> dict[str, Any]:
        """JSON-safe snapshot of the full row (for delta old/new state)."""
        return {
            "id": self.id,
            "url": self.url,
            "slug": self.slug,
            "note": self.note,
            "familiarity": self.familiarity,
            "importance": self.importance,
            "last_reviewed": self.last_reviewed.isoformat() if self.last_reviewed else None,
            "next_review": self.next_review.isoformat() if self.next_review else None,
            "review_count": self.review_count,
            "ease_factor": self.ease_factor,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "title": self.title,
            "difficulty": self.difficulty,
            "tags": self.tags,
        }

    @classmethod
    def from_state_dict(cls, d: dict[str, Any]) -> "Problem":
        """Rebuild a Problem from a ``to_state_dict`` snapshot (used by undo/import)."""

        def _dt(v):
            return datetime.fromisoformat(v) if v else None

        def _d(v):
            return date.fromisoformat(v) if v else None

        return cls(
            id=d["id"],
            url=d["url"],
            slug=d["slug"],
            note=d.get("note", ""),
            familiarity=d["familiarity"],
            importance=d["importance"],
            last_reviewed=_d(d["last_reviewed"]),
            next_review=_d(d["next_review"]),
            review_count=d["review_count"],
            ease_factor=d["ease_factor"],
            created_at=_dt(d["created_at"]),
            updated_at=_dt(d["updated_at"]),
            title=d.get("title"),
            difficulty=d.get("difficulty"),
            tags=d.get("tags"),
        )


class Delta(Base):
    __tablename__ = "deltas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action: Mapped[str] = mapped_column(String, nullable=False)  # add | update | delete
    question_id: Mapped[int] = mapped_column(Integer, nullable=False)
    old_state: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    new_state: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[Any] = mapped_column(JSON, nullable=False)


class Owner(Base):
    __tablename__ = "owner"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # always 1 (single-owner)
    github_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    github_login: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
