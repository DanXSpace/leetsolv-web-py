"""Faithful port of leetsolv's scheduler.

leetsolv (github.com/eannchen/leetsolv) is a Go CLI using a custom SM-2
variant. This module ports `core/scheduler.go`, `core/model.go`, and the
defaults in `config/config.go` to Python. The deterministic parts are meant
to match bit-for-bit; only `RandomizeInterval`'s jitter is distributional
rather than sequence-identical (see docs/adr/0001-port-leetsolv-scheduler.md).

All scheduling takes `today` as an explicit argument so the caller controls
the "what is today" boundary. leetsolv itself uses the current UTC date.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from datetime import date, timedelta
from enum import IntEnum


class Importance(IntEnum):
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3


class Familiarity(IntEnum):
    VERY_HARD = 0
    HARD = 1
    MEDIUM = 2
    EASY = 3
    VERY_EASY = 4


class MemoryUse(IntEnum):
    REASONED = 0
    PARTIAL = 1
    FULL = 2


# Interval settings (days) -- core/scheduler.go
MAX_INTERVAL = 90
BASE_INTERVALS: dict[Importance, int] = {
    Importance.LOW: 8,
    Importance.MEDIUM: 6,
    Importance.HIGH: 5,
    Importance.CRITICAL: 4,
}
MEMORY_MULTIPLIERS: dict[MemoryUse, float] = {
    MemoryUse.REASONED: 1.00,
    MemoryUse.PARTIAL: 1.10,
    MemoryUse.FULL: 1.25,
}

# Ease factor settings -- core/scheduler.go
MIN_EASE_FACTOR = 1.3
MAX_EASE_FACTOR = 2.6
START_EASE_FACTORS: dict[Importance, float] = {
    Importance.LOW: 2.0,
    Importance.MEDIUM: 1.9,
    Importance.HIGH: 1.8,
    Importance.CRITICAL: 1.7,
}
IMPORTANCE_EASE_BONUS: dict[Importance, float] = {
    Importance.LOW: 0.15,
    Importance.MEDIUM: 0.10,
    Importance.HIGH: 0.05,
    Importance.CRITICAL: 0.03,
}
FAMILIARITY_EASE_PENALTY: dict[Familiarity, float] = {
    Familiarity.VERY_HARD: -0.40,
    Familiarity.HARD: -0.25,
    Familiarity.MEDIUM: -0.10,
    Familiarity.EASY: 0.05,
    Familiarity.VERY_EASY: 0.15,
}
MEMORY_EASE_PENALTY: dict[MemoryUse, float] = {
    MemoryUse.REASONED: 0.00,
    MemoryUse.PARTIAL: -0.02,
    MemoryUse.FULL: -0.05,
}

# Due priority-list scoring weights -- config/config.go
IMPORTANCE_WEIGHT = 1.5
OVERDUE_WEIGHT = 0.5
FAMILIARITY_WEIGHT = 3.0
REVIEW_PENALTY_WEIGHT = -1.5
EASE_PENALTY_WEIGHT = -1.0


@dataclass
class Question:
    id: int
    url: str
    note: str
    familiarity: Familiarity
    importance: Importance
    last_reviewed: date
    next_review: date
    review_count: int
    ease_factor: float


def go_round(x: float) -> int:
    """math.Round (Go): nearest integer, rounding half away from zero."""
    if x >= 0:
        return int(math.floor(x + 0.5))
    return int(math.ceil(x - 0.5))


class Scheduler:
    """Port of core.SM2Scheduler."""

    def __init__(
        self,
        *,
        randomize_interval: bool = True,
        overdue_penalty: bool = False,
        overdue_limit: int = 7,
        rng: random.Random | None = None,
    ) -> None:
        self.randomize_interval = randomize_interval
        self.overdue_penalty = overdue_penalty
        self.overdue_limit = overdue_limit
        self._rng = rng if rng is not None else random.Random()

    def _intn(self, n: int) -> int:
        # Go rand.IntN(n) -> [0, n)
        return self._rng.randrange(n)

    def schedule_new(self, q: Question, memory: MemoryUse, today: date) -> Question:
        q.ease_factor = START_EASE_FACTORS[q.importance]
        q.review_count = 1
        q.last_reviewed = today

        interval_days = BASE_INTERVALS[q.importance]
        if q.familiarity == Familiarity.VERY_EASY:
            interval_days += 7
        elif q.familiarity == Familiarity.EASY:
            interval_days += 5
        elif q.familiarity == Familiarity.MEDIUM:
            interval_days += 2
        interval_days = go_round(interval_days * MEMORY_MULTIPLIERS[memory])

        self._set_next_review(q, today, interval_days)
        return q

    def schedule(self, q: Question, memory: MemoryUse, today: date) -> Question:
        q.review_count += 1
        base_interval = BASE_INTERVALS[q.importance]

        # Reset if still struggling
        if q.familiarity == Familiarity.VERY_HARD:
            self._set_next_review(q, today, base_interval)
            self._set_ease_factor(q, memory)
            q.last_reviewed = today
            return q

        # Penalty for being overdue
        if self.overdue_penalty:
            self._apply_overdue_penalty(q, today)

        # Growth based on last interval x ease factor x memory use
        prev_interval_days = (q.next_review - q.last_reviewed).days
        if prev_interval_days < 1:
            prev_interval_days = base_interval
        interval_days = go_round(prev_interval_days * q.ease_factor * MEMORY_MULTIPLIERS[memory])

        self._set_next_review(q, today, interval_days)
        self._set_ease_factor(q, memory)
        q.last_reviewed = today
        return q

    def _set_next_review(self, q: Question, today: date, interval_days: int) -> None:
        # Randomize interval to avoid over-fitting to a specific date
        if self.randomize_interval:
            interval_days += self._intn(4) - 1

        # Secure bounds
        if interval_days < 1:
            interval_days = 1
        elif interval_days > MAX_INTERVAL:
            interval_days = MAX_INTERVAL

        q.next_review = today + timedelta(days=interval_days)

    def _set_ease_factor(self, q: Question, memory: MemoryUse) -> None:
        bonus = IMPORTANCE_EASE_BONUS[q.importance]
        penalty = FAMILIARITY_EASE_PENALTY[q.familiarity]
        memory_penalty = MEMORY_EASE_PENALTY[memory]

        q.ease_factor += bonus
        q.ease_factor += penalty
        q.ease_factor += memory_penalty

        # Encourage stability if consistently good
        if q.review_count >= 3 and q.familiarity >= Familiarity.MEDIUM and memory == MemoryUse.REASONED:
            q.ease_factor += bonus * 0.5

        # Secure bounds
        if q.ease_factor < MIN_EASE_FACTOR:
            q.ease_factor = MIN_EASE_FACTOR
        elif q.ease_factor > MAX_EASE_FACTOR:
            q.ease_factor = MAX_EASE_FACTOR

    def _apply_overdue_penalty(self, q: Question, today: date) -> None:
        overdue_days = (today - q.next_review).days
        if (
            overdue_days > self.overdue_limit
            and q.importance > Importance.LOW
            and q.familiarity < Familiarity.VERY_EASY
        ):
            penalty_factor = min((overdue_days - self.overdue_limit) * 0.01, 0.1)
            q.ease_factor -= penalty_factor

    def priority_score(self, q: Question, today: date) -> float:
        overdue_days = (today - q.next_review).days
        if overdue_days < 0:
            overdue_days = 0

        # Invert familiarity: VeryEasy = 0, VeryHard = 4
        fam_score = 4 - int(q.familiarity)

        return (
            IMPORTANCE_WEIGHT * int(q.importance)
            + OVERDUE_WEIGHT * overdue_days
            + FAMILIARITY_WEIGHT * fam_score
            + REVIEW_PENALTY_WEIGHT * q.review_count
            + EASE_PENALTY_WEIGHT * q.ease_factor
        )
