"""Parse leetsolv's on-disk JSON into leetsolv-web rows.

leetsolv persists two files under ``~/.leetsolv/``:

- ``questions.json`` — ``{"max_id": N, "questions": {"<id>": {Question}}, ...}``
- ``deltas.json``   — a JSON array of ``{action, question_id, old_state, new_state, created_at}``

The ``Question``/delta-state shapes are defined by leetsolv's ``core/model.go``
and store the *same 0-based enums* as our ``app.scheduler`` (familiarity
0..4, importance 0..3), so values map across unchanged. Timestamps are
RFC3339 (with nanosecond precision); our columns store naive-UTC datetimes
and ``date`` for the review dates, so we parse to UTC and drop the offset.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from app.enrich import enrich_problem
from app.models import Delta, Problem
from app.urls import parse_leetcode_url


def _as_datetime(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).replace(tzinfo=None)


def _as_date(s: str) -> date:
    return _as_datetime(s).date()


def question_from_leetsolv(d: dict[str, Any]) -> Problem:
    """Build a :class:`Problem` (enriched) from one leetsolv question dict."""
    _, url = parse_leetcode_url(d["url"])
    p = Problem(
        id=d["id"],
        url=url,
        slug=d["url"].rstrip("/").rsplit("/", 1)[-1],
        note=d.get("note", ""),
        familiarity=d["familiarity"],
        importance=d["importance"],
        last_reviewed=_as_date(d["last_reviewed"]),
        next_review=_as_date(d["next_review"]),
        review_count=d["review_count"],
        ease_factor=d["ease_factor"],
        created_at=_as_datetime(d["created_at"]),
        updated_at=_as_datetime(d["updated_at"]),
    )
    return enrich_problem(p)


def parse_questions(raw: dict[str, Any]) -> list[Problem]:
    """Parse a leetsolv ``questions.json`` object into Problems (id order)."""
    questions = raw.get("questions") or {}
    rows = [question_from_leetsolv(q) for q in questions.values()]
    rows.sort(key=lambda p: p.id)
    return rows


def delta_from_leetsolv(d: dict[str, Any]) -> Delta:
    """Build a :class:`Delta` from one leetsolv delta dict.

    ``old_state``/``new_state`` are converted into our snapshot shape (via
    ``Problem.to_state_dict``) so ``undo`` can restore them with
    ``Problem.from_state_dict``.
    """
    old = d.get("old_state")
    new = d.get("new_state")
    return Delta(
        action=d["action"],
        question_id=d["question_id"],
        old_state=question_from_leetsolv(old).to_state_dict() if old else None,
        new_state=question_from_leetsolv(new).to_state_dict() if new else None,
        created_at=_as_datetime(d["created_at"]),
    )


def parse_deltas(raw: list[dict[str, Any]]) -> list[Delta]:
    """Parse a leetsolv ``deltas.json`` array into Deltas."""
    return [delta_from_leetsolv(d) for d in raw]
