"""Tests for the leetsolv JSON import (M5)."""

from datetime import date, datetime

from app.importer import parse_deltas, parse_questions
from app.models import Delta, Problem
from app.service import QuestionService

TWO_SUM = "https://leetcode.com/problems/two-sum/"
SORT_COLORS = "https://leetcode.com/problems/sort-colors/"


def _q(id_, url, note=""):
    return {
        "id": id_,
        "url": url,
        "note": note,
        "familiarity": 1,  # Hard (0-based parity with leetsolv)
        "importance": 2,  # High
        "last_reviewed": "2026-10-01T00:00:00Z",
        "next_review": "2026-10-05T00:00:00Z",
        "review_count": 1,
        "ease_factor": 1.8,
        "updated_at": "2026-10-01T03:07:12.418718369Z",
        "created_at": "2026-10-01T03:07:12.4187186Z",
    }


def _questions_obj():
    return {
        "max_id": 2,
        "questions": {"1": _q(1, TWO_SUM, "hashmap"), "2": _q(2, SORT_COLORS, "dutch flag")},
        # url_index / tries are ignored by the importer
        "url_index": {},
        "url_trie": {},
        "note_trie": {},
    }


def _deltas_obj():
    return [
        {
            "action": "add",
            "question_id": 1,
            "old_state": None,
            "new_state": _q(1, TWO_SUM, "hashmap"),
            "created_at": "2026-10-01T03:07:12.41876653Z",
        },
        {
            "action": "add",
            "question_id": 2,
            "old_state": None,
            "new_state": _q(2, SORT_COLORS, "dutch flag"),
            "created_at": "2026-10-01T03:10:04.064151019Z",
        },
    ]


def test_parse_questions_converts_and_enriches():
    problems = parse_questions(_questions_obj())
    assert [p.id for p in problems] == [1, 2]
    two = problems[0]
    assert two.slug == "two-sum"
    assert two.url == TWO_SUM
    assert two.note == "hashmap"
    assert two.familiarity == 1  # unchanged (leetsolv stores the same 0-based enum)
    assert two.importance == 2
    assert two.ease_factor == 1.8
    assert two.last_reviewed == date(2026, 10, 1)
    assert two.next_review == date(2026, 10, 5)
    assert two.created_at == datetime(2026, 10, 1, 3, 7, 12, 418718)
    # enriched from the bundled dataset
    assert two.title == "Two Sum"
    assert two.difficulty == "Easy"
    assert two.tags == ["Array", "Hash Table"]


def test_parse_deltas_converts_to_our_state_shape():
    deltas = parse_deltas(_deltas_obj())
    assert [d.action for d in deltas] == ["add", "add"]
    assert deltas[0].question_id == 1
    assert deltas[0].old_state is None
    assert deltas[0].created_at == datetime(2026, 10, 1, 3, 7, 12, 418766)
    # new_state must round-trip through Problem.from_state_dict (used by undo)
    restored = Problem.from_state_dict(deltas[0].new_state)
    assert restored.slug == "two-sum"
    assert restored.note == "hashmap"
    assert restored.familiarity == 1
    assert restored.next_review == date(2026, 10, 5)


def test_import_leetsolv_inserts_and_writes_history(session):
    svc = QuestionService(session)
    summary = svc.import_leetsolv(_questions_obj(), _deltas_obj())
    assert summary["imported"] == 2
    assert summary["skipped"] == 0
    assert summary["deltas"] == 2

    problems = svc.list_all()
    assert {p.id for p in problems} == {1, 2}
    assert problems[0].title in ("Two Sum", "Sort Colors")  # enriched
    assert len(svc.history()) == 2


def test_import_leetsolv_is_idempotent(session):
    svc = QuestionService(session)
    svc.import_leetsolv(_questions_obj(), _deltas_obj())
    summary = svc.import_leetsolv(_questions_obj(), _deltas_obj())
    assert summary["imported"] == 0
    assert summary["skipped"] == 2
    assert summary["deltas"] == 0
    assert len(svc.list_all()) == 2
    assert len(svc.history()) == 2  # no duplicated history


def test_import_leetsolv_backfills_existing_unenriched(session):
    # A row added before enrichment existed (title/difficulty/tags null).
    existing = Problem(
        id=100,  # high id so it doesn't collide with imported ids 1,2
        url="https://leetcode.com/problems/valid-palindrome/",
        slug="valid-palindrome",
        note="",
        familiarity=1,
        importance=2,
        last_reviewed=date(2026, 10, 1),
        next_review=date(2026, 10, 7),
        review_count=1,
        ease_factor=1.8,
        created_at=datetime(2026, 10, 1, 9, 0, 0),
        updated_at=datetime(2026, 10, 1, 9, 0, 0),
    )
    session.add(existing)
    session.commit()

    svc = QuestionService(session)
    summary = svc.import_leetsolv(_questions_obj(), _deltas_obj())
    assert summary["imported"] == 2
    assert summary["enriched"] == 1

    session.refresh(existing)
    assert existing.title == "Valid Palindrome"
    assert existing.difficulty == "Easy"
    assert existing.tags == ["Two Pointers", "String"]
