"""LeetCode metadata enrichment from the bundled static dataset.

LeetCode has no stable public REST API, so title/difficulty/tags ship as a
static community dataset (``app/data/leetcode_metadata.json``) built by
``scripts/build_metadata.py``. This module loads that dataset and applies it
to a :class:`~app.models.Problem` row by slug.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.models import Problem

_DATA_PATH = Path(__file__).with_name("data") / "leetcode_metadata.json"


@lru_cache(maxsize=1)
def _dataset() -> dict[str, dict[str, Any]]:
    with _DATA_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def lookup(slug: str) -> dict[str, Any] | None:
    """Return ``{"title", "difficulty", "tags"}`` for a slug, or ``None``."""
    return _dataset().get(slug)


def enrich_problem(p: Problem) -> Problem:
    """Fill a problem's title/difficulty/tags from its slug, if available.

    Never overwrites metadata that is already present, so a re-import or
    review of an already-enriched row is a no-op.
    """
    meta = lookup(p.slug)
    if meta is None:
        return p
    if p.title is None:
        p.title = meta["title"]
    if p.difficulty is None:
        p.difficulty = meta["difficulty"]
    if p.tags is None:
        p.tags = meta["tags"]
    return p
