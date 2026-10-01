"""Tests for the leetsolv scheduler port.

Expected values are derived from leetsolv's `core/scheduler.go` and from the
author's real `~/.leetsolv/questions.json` (extracted 2026-09-30).
"""

from datetime import date, timedelta

import pytest

from app.scheduler import (
    Familiarity,
    Importance,
    MemoryUse,
    Question,
    Scheduler,
    go_round,
)


def _q(**overrides):
    base = dict(
        id=1,
        url="https://leetcode.com/problems/two-sum/",
        note="",
        familiarity=Familiarity.HARD,
        importance=Importance.HIGH,
        last_reviewed=date(2026, 10, 1),
        next_review=date(2026, 10, 6),
        review_count=1,
        ease_factor=1.8,
    )
    base.update(overrides)
    return Question(**base)


class _FixedRng:
    """Deterministic stand-in for Go's Rand (IntN -> [0, n))."""

    def __init__(self, value):
        self.value = value

    def randrange(self, n):
        return self.value


def _scheduler(randomize=False, rng=None, **kw):
    return Scheduler(randomize_interval=randomize, rng=rng, **kw)


# --- schedule_new ---


def test_schedule_new_deterministic():
    q = _q(familiarity=Familiarity.HARD, importance=Importance.HIGH)
    _scheduler().schedule_new(q, MemoryUse.REASONED, date(2026, 10, 1))
    assert q.ease_factor == 1.8  # start EF for High importance
    assert q.review_count == 1
    assert q.last_reviewed == date(2026, 10, 1)
    assert q.next_review == date(2026, 10, 6)  # base 5, no jitter


def test_schedule_new_familiarity_bonuses():
    cases = {
        Familiarity.VERY_EASY: 12,  # 5 + 7
        Familiarity.EASY: 10,  # 5 + 5
        Familiarity.MEDIUM: 7,  # 5 + 2
        Familiarity.HARD: 5,
        Familiarity.VERY_HARD: 5,
    }
    for fam, days in cases.items():
        q = _q(familiarity=fam, importance=Importance.HIGH)
        _scheduler().schedule_new(q, MemoryUse.REASONED, date(2026, 10, 1))
        assert q.next_review == date(2026, 10, 1) + timedelta(days=days), fam


def test_schedule_new_memory_multipliers():
    cases = {
        MemoryUse.REASONED: 6,  # round(6 * 1.00) = 6
        MemoryUse.PARTIAL: 7,  # round(6 * 1.10) = round(6.6) = 7
        MemoryUse.FULL: 8,  # round(6 * 1.25) = round(7.5) = 8 (half away from zero)
    }
    for mem, days in cases.items():
        q = _q(familiarity=Familiarity.HARD, importance=Importance.MEDIUM)
        _scheduler().schedule_new(q, mem, date(2026, 10, 1))
        assert q.next_review == date(2026, 10, 1) + timedelta(days=days), mem


def test_go_round_half_away_from_zero():
    assert go_round(4.5) == 5
    assert go_round(5.5) == 6
    assert go_round(2.5) == 3
    assert go_round(-2.5) == -3
    assert go_round(0.5) == 1
    assert go_round(6.25) == 6


# --- schedule (review) ---


def test_schedule_review_growth_and_ease():
    q = _q(
        familiarity=Familiarity.MEDIUM,
        importance=Importance.HIGH,
        last_reviewed=date(2026, 10, 1),
        next_review=date(2026, 10, 6),
        review_count=2,
        ease_factor=1.85,
    )
    _scheduler().schedule(q, MemoryUse.REASONED, date(2026, 10, 11))
    # prev interval 5; interval = round(5 * 1.85 * 1.0) = round(9.25) = 9
    assert q.next_review == date(2026, 10, 20)
    assert q.review_count == 3
    # EF: +0.05 (High) -0.10 (Medium) +0.0 = -0.05; stability +0.05*0.5 = 0.025
    assert q.ease_factor == pytest.approx(1.825, rel=1e-12)


def test_schedule_very_hard_resets_and_clamps():
    q = _q(
        familiarity=Familiarity.VERY_HARD,
        importance=Importance.HIGH,
        review_count=3,
        ease_factor=1.5,
    )
    _scheduler().schedule(q, MemoryUse.REASONED, date(2026, 10, 11))
    # reset to base interval (5), no growth
    assert q.next_review == date(2026, 10, 16)
    # EF: 1.5 + 0.05 - 0.40 + 0.0 = 1.15 -> clamp 1.3
    assert q.ease_factor == 1.3
    assert q.review_count == 4


def test_schedule_overdue_penalty():
    q = _q(
        familiarity=Familiarity.MEDIUM,
        importance=Importance.HIGH,
        last_reviewed=date(2026, 10, 1),
        next_review=date(2026, 10, 6),
        review_count=2,
        ease_factor=1.9,
    )
    s = Scheduler(randomize_interval=False, overdue_penalty=True, overdue_limit=7)
    s.schedule(q, MemoryUse.REASONED, date(2026, 10, 16))  # 10 days overdue
    # penalty: min((10-7)*0.01, 0.1) = 0.03 -> EF 1.87; interval = round(5*1.87) = 9
    assert q.next_review == date(2026, 10, 25)
    # EF: 1.87 + 0.05 - 0.10 + 0.0 + 0.025 = 1.845
    assert q.ease_factor == pytest.approx(1.845, rel=1e-12)


# --- priority score ---


def test_priority_score():
    q = _q(
        familiarity=Familiarity.HARD,  # fam score 3
        importance=Importance.HIGH,  # 2
        next_review=date(2026, 10, 10),  # overdue 1 vs today 10-11
        review_count=2,
        ease_factor=1.8,
    )
    score = Scheduler().priority_score(q, date(2026, 10, 11))
    assert score == pytest.approx(7.7, rel=1e-12)


# --- reconciliation with real data ---

REAL_QUESTIONS = [
    # extracted from ~/.leetsolv/questions.json, 2026-09-30 (all: familiarity=1
    # Hard, importance=2 High, review_count=1, ease_factor=1.8)
    {"url": "https://leetcode.com/problems/remove-duplicates-from-sorted-array-ii/", "next_review": date(2026, 10, 5)},
    {"url": "https://leetcode.com/problems/valid-palindrome/", "next_review": date(2026, 10, 7)},
    {"url": "https://leetcode.com/problems/sort-colors/", "next_review": date(2026, 10, 5)},
    {"url": "https://leetcode.com/problems/merge-sorted-array/", "next_review": date(2026, 10, 5)},
]


def test_real_data_matches_deterministic_schedule_new():
    today = date(2026, 10, 1)
    for r in REAL_QUESTIONS:
        q = _q(
            url=r["url"],
            familiarity=Familiarity.HARD,
            importance=Importance.HIGH,
            last_reviewed=today,
            next_review=today,
            review_count=0,
            ease_factor=0.0,
        )
        _scheduler().schedule_new(q, MemoryUse.REASONED, today)
        assert q.ease_factor == 1.8  # start EF for High importance (matches real)
        assert q.review_count == 1  # matches real
        # real next_review must sit within the jitter window [base-1, base+2]
        det_next = q.next_review  # today + 5
        assert det_next - timedelta(days=1) <= r["next_review"] <= det_next + timedelta(days=2)


def test_jitter_reproduces_real_intervals():
    today = date(2026, 10, 1)
    # rand=0 -> jitter -1 -> 5-1 = 4 (matches 3 of the 4 real questions)
    q1 = _q(importance=Importance.HIGH, familiarity=Familiarity.HARD)
    Scheduler(randomize_interval=True, rng=_FixedRng(0)).schedule_new(q1, MemoryUse.REASONED, today)
    assert q1.next_review == date(2026, 10, 5)

    # rand=2 -> jitter +1 -> 5+1 = 6 (matches valid-palindrome)
    q2 = _q(importance=Importance.HIGH, familiarity=Familiarity.HARD)
    Scheduler(randomize_interval=True, rng=_FixedRng(2)).schedule_new(q2, MemoryUse.REASONED, today)
    assert q2.next_review == date(2026, 10, 7)
