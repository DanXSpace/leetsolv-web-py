"""Tests for the service layer (leetsolv QuestionUseCase port)."""

from datetime import date, datetime

import pytest

from app.models import Problem
from app.scheduler import Familiarity, Importance, MemoryUse
from app.service import NoActionError, NotFoundError, QuestionService

TODAY = date(2026, 10, 11)
URL = "https://leetcode.com/problems/two-sum"


@pytest.fixture
def svc(session, deterministic_scheduler):
    return QuestionService(
        session,
        deterministic_scheduler,
        today=lambda: TODAY,
        now=lambda: datetime(2026, 10, 11, 9, 0, 0),
    )


def _add_problem(session, url, slug, next_review, **kw):
    base = dict(
        url=url,
        slug=slug,
        note="",
        familiarity=1,
        importance=2,
        last_reviewed=date(2026, 10, 1),
        next_review=next_review,
        review_count=1,
        ease_factor=1.8,
        created_at=datetime(2026, 10, 1, 9, 0, 0),
        updated_at=datetime(2026, 10, 1, 9, 0, 0),
    )
    base.update(kw)
    p = Problem(**base)
    session.add(p)
    return p


# --- upsert (add) ---


def test_add_new_problem(svc):
    p, delta = svc.upsert(URL, "use hashmap", Familiarity.HARD, Importance.HIGH, MemoryUse.REASONED)
    assert p.id is not None
    assert p.slug == "two-sum"
    assert p.ease_factor == 1.8
    assert p.review_count == 1
    assert p.last_reviewed == TODAY
    assert p.next_review == date(2026, 10, 16)  # base 5, no jitter
    assert delta.action == "add"
    assert delta.new_state["id"] == p.id
    assert delta.old_state is None


# --- upsert (review) ---


def test_review_updates_and_schedules(svc):
    svc.upsert(URL, "orig", Familiarity.HARD, Importance.HIGH, MemoryUse.REASONED)
    p2, delta = svc.upsert(URL, "better note", Familiarity.MEDIUM, Importance.HIGH, MemoryUse.REASONED)
    assert len(svc.list_all()) == 1  # dedup by URL, not a new row
    assert p2.note == "better note"
    assert p2.familiarity == int(Familiarity.MEDIUM)
    assert p2.review_count == 2
    # interval = round(prev(5) * EF(1.8) * 1.0) = 9 -> TODAY + 9
    assert p2.next_review == date(2026, 10, 20)
    # EF: 1.8 + 0.05 (High) - 0.10 (Medium) = 1.75
    assert p2.ease_factor == pytest.approx(1.75, rel=1e-12)
    assert delta.action == "update"
    assert delta.old_state["familiarity"] == int(Familiarity.HARD)
    assert delta.old_state["note"] == "orig"


def test_very_hard_review_resets(svc):
    svc.upsert(URL, "", Familiarity.HARD, Importance.HIGH, MemoryUse.REASONED)
    p, _ = svc.upsert(URL, "", Familiarity.VERY_HARD, Importance.HIGH, MemoryUse.REASONED)
    assert p.next_review == date(2026, 10, 16)  # reset to base interval 5
    assert p.review_count == 2
    # EF: 1.8 + 0.05 - 0.40 = 1.45
    assert p.ease_factor == pytest.approx(1.45, rel=1e-12)


# --- delete / undo / history ---


def test_delete(svc):
    p, _ = svc.upsert(URL, "", Familiarity.HARD, Importance.HIGH, MemoryUse.REASONED)
    svc.delete(p.id)
    assert svc.list_all() == []
    assert svc.history()[0].action == "delete"


def test_edit_note_preserves_schedule(svc):
    p, _ = svc.upsert(URL, "orig", Familiarity.HARD, Importance.HIGH, MemoryUse.REASONED)
    p2 = svc.edit_note(p.id, "new note")
    assert p2.note == "new note"
    assert p2.review_count == 1
    assert p2.next_review == date(2026, 10, 16)
    svc.undo()
    assert svc.get(p.id).note == "orig"


def test_undo_add(svc):
    p, _ = svc.upsert(URL, "", Familiarity.HARD, Importance.HIGH, MemoryUse.REASONED)
    svc.undo()
    assert svc.list_all() == []
    assert svc.history() == []


def test_undo_update_restores_previous_state(svc):
    p, _ = svc.upsert(URL, "orig", Familiarity.HARD, Importance.HIGH, MemoryUse.REASONED)
    svc.upsert(URL, "changed", Familiarity.MEDIUM, Importance.HIGH, MemoryUse.REASONED)
    svc.undo()
    restored = svc.get(p.id)
    assert restored.note == "orig"
    assert restored.familiarity == int(Familiarity.HARD)
    assert restored.review_count == 1


def test_undo_delete_restores_problem(svc):
    p, _ = svc.upsert(URL, "note", Familiarity.HARD, Importance.HIGH, MemoryUse.REASONED)
    svc.delete(p.id)
    assert svc.list_all() == []
    svc.undo()
    restored = svc.get(p.id)
    assert restored.id == p.id
    assert restored.note == "note"


def test_undo_empty_raises(svc):
    with pytest.raises(NoActionError):
        svc.undo()


def test_history_most_recent_first(svc):
    svc.upsert("https://leetcode.com/problems/two-sum", "", Familiarity.HARD, Importance.HIGH, MemoryUse.REASONED)
    svc.upsert("https://leetcode.com/problems/sort-colors", "", Familiarity.HARD, Importance.HIGH, MemoryUse.REASONED)
    h = svc.history()
    assert [d.action for d in h] == ["add", "add"]
    assert h[0].question_id > h[1].question_id  # most recent first


# --- status summary ---


def test_status_summary_buckets(svc):
    s = svc.session
    _add_problem(s, "https://leetcode.com/problems/a/", "a", date(2026, 10, 10))  # due
    _add_problem(s, "https://leetcode.com/problems/b/", "b", date(2026, 10, 11))  # due (today)
    _add_problem(s, "https://leetcode.com/problems/c/", "c", date(2026, 10, 12))  # upcoming
    _add_problem(s, "https://leetcode.com/problems/d/", "d", date(2026, 10, 20))  # future
    s.commit()
    summary = svc.status_summary()
    assert summary["total"] == 4
    assert summary["total_due"] == 2
    assert summary["total_upcoming"] == 1
    assert {p.slug for p in summary["due"]} == {"a", "b"}
    assert {p.slug for p in summary["upcoming"]} == {"c"}


# --- search ---


def test_search_query_and_filters(svc):
    s = svc.session
    _add_problem(s, "https://leetcode.com/problems/two-sum/", "two-sum", date(2026, 10, 11))
    _add_problem(s, "https://leetcode.com/problems/valid-palindrome/", "valid-palindrome", date(2026, 10, 11))
    s.commit()
    assert {p.slug for p in svc.search(query="two")} == {"two-sum"}
    assert {p.slug for p in svc.search(familiarity=1)} == {"two-sum", "valid-palindrome"}
    assert {p.slug for p in svc.search(due_only=True)} == {"two-sum", "valid-palindrome"}


# --- get / settings ---


def test_get_by_id_and_url(svc):
    p, _ = svc.upsert(URL, "", Familiarity.HARD, Importance.HIGH, MemoryUse.REASONED)
    assert svc.get(p.id).slug == "two-sum"
    assert svc.get("https://leetcode.com/problems/two-sum/").id == p.id
    with pytest.raises(NotFoundError):
        svc.get(999)


def test_settings_roundtrip(svc):
    assert svc.get_setting("overdue_limit", 7) == 7
    svc.set_setting("overdue_limit", 14)
    assert svc.get_setting("overdue_limit") == 14
