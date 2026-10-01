"""Tests for the bundled LeetCode metadata enrichment."""

from app.enrich import enrich_problem, lookup
from app.models import Problem


def test_lookup_known_slug():
    meta = lookup("two-sum")
    assert meta["title"] == "Two Sum"
    assert meta["difficulty"] == "Easy"
    assert meta["tags"] == ["Array", "Hash Table"]


def test_lookup_unknown_slug_is_none():
    assert lookup("definitely-not-a-real-slug") is None


def test_enrich_problem_fills_metadata():
    p = Problem(slug="sort-colors")
    enrich_problem(p)
    assert p.title == "Sort Colors"
    assert p.difficulty == "Medium"
    assert p.tags == ["Array", "Two Pointers", "Sorting"]


def test_enrich_problem_does_not_overwrite():
    p = Problem(slug="two-sum", title="Custom", difficulty="Hard", tags=["X"])
    enrich_problem(p)
    assert p.title == "Custom"
    assert p.difficulty == "Hard"
    assert p.tags == ["X"]


def test_enrich_problem_unknown_slug_is_noop():
    p = Problem(slug="not-a-real-problem-slug")
    enrich_problem(p)
    assert p.title is None
    assert p.difficulty is None
    assert p.tags is None
