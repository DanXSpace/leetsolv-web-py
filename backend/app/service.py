"""Application service layer: port of leetsolv's QuestionUseCase.

Wires the DB models to the scheduler and reproduces leetsolv's operations
(add/review via upsert, delete, undo, history, status summary, search,
settings). `today` and `now` are injectable so tests can pin time.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import Delta, Problem, Setting
from app.scheduler import Familiarity, Importance, MemoryUse, Question, Scheduler
from app.urls import parse_leetcode_url


def today_utc() -> date:
    return datetime.now(timezone.utc).date()


def now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class NotFoundError(LookupError):
    pass


class NoActionError(LookupError):
    pass


class QuestionService:
    def __init__(
        self,
        session: Session,
        scheduler: Scheduler | None = None,
        *,
        top_k_due: int = 10,
        top_k_upcoming: int = 10,
        today: Callable[[], date] = today_utc,
        now: Callable[[], datetime] = now_utc,
    ) -> None:
        self.session = session
        self.scheduler = scheduler or Scheduler()
        self.top_k_due = top_k_due
        self.top_k_upcoming = top_k_upcoming
        self._today = today
        self._now = now

    # -- queries --

    def get(self, target) -> Problem:
        return self._find(target)

    def list_all(self) -> list[Problem]:
        return list(self.session.scalars(select(Problem).order_by(Problem.id.desc())).all())

    def history(self) -> list[Delta]:
        return list(self.session.scalars(select(Delta).order_by(Delta.id.desc())).all())

    def status_summary(self) -> dict[str, Any]:
        problems = list(self.session.scalars(select(Problem)).all())
        today = self._today()
        one_day = today + timedelta(days=1)
        due: list[tuple[float, Problem]] = []
        upcoming: list[tuple[float, Problem]] = []
        for p in problems:
            q = self._to_question(p)
            if p.next_review <= today:
                due.append((self.scheduler.priority_score(q, today), p))
            elif p.next_review <= one_day:
                upcoming.append((self.scheduler.priority_score(q, today), p))
        due.sort(key=lambda x: -x[0])
        upcoming.sort(key=lambda x: -x[0])
        return {
            "total": len(problems),
            "total_due": len(due),
            "total_upcoming": len(upcoming),
            "due": [p for _, p in due[: self.top_k_due]],
            "upcoming": [p for _, p in upcoming[: self.top_k_upcoming]],
        }

    def search(
        self,
        query: str | None = None,
        familiarity: int | None = None,
        importance: int | None = None,
        review_count: int | None = None,
        due_only: bool = False,
    ) -> list[Problem]:
        stmt = select(Problem)
        if familiarity is not None:
            stmt = stmt.where(Problem.familiarity == familiarity)
        if importance is not None:
            stmt = stmt.where(Problem.importance == importance)
        if review_count is not None:
            stmt = stmt.where(Problem.review_count == review_count)
        if query:
            like = f"%{query.lower()}%"
            stmt = stmt.where(or_(Problem.slug.like(like), Problem.note.like(like)))
        results = list(self.session.scalars(stmt).all())
        if due_only:
            today = self._today()
            results = [p for p in results if p.next_review <= today]
        return results

    # -- mutations --

    def upsert(
        self,
        raw_url: str,
        note: str,
        familiarity: Familiarity,
        importance: Importance,
        memory: MemoryUse,
    ) -> tuple[Problem, Delta]:
        slug, url = parse_leetcode_url(raw_url)
        today = self._today()
        now = self._now()

        existing = self.session.scalar(select(Problem).where(Problem.url == url))
        if existing is not None:
            old_state = existing.to_state_dict()
            q = Question(
                id=existing.id,
                url=url,
                note=note,
                familiarity=familiarity,
                importance=importance,
                last_reviewed=existing.last_reviewed,
                next_review=existing.next_review,
                review_count=existing.review_count,
                ease_factor=existing.ease_factor,
            )
            self.scheduler.schedule(q, memory, today)
            self._apply_schedule(existing, q)
            existing.note = note
            existing.updated_at = now
            self.session.flush()
            delta = Delta(
                action="update",
                question_id=existing.id,
                old_state=old_state,
                new_state=existing.to_state_dict(),
                created_at=now,
            )
            self.session.add(delta)
            self.session.commit()
            return existing, delta

        p = Problem(
            url=url,
            slug=slug,
            note=note,
            familiarity=int(familiarity),
            importance=int(importance),
            last_reviewed=today,
            next_review=today,
            review_count=0,
            ease_factor=0.0,
            created_at=now,
            updated_at=now,
        )
        q = Question(
            id=0,
            url=url,
            note=note,
            familiarity=familiarity,
            importance=importance,
            last_reviewed=today,
            next_review=today,
            review_count=0,
            ease_factor=0.0,
        )
        self.scheduler.schedule_new(q, memory, today)
        self._apply_schedule(p, q)
        self.session.add(p)
        self.session.flush()
        delta = Delta(
            action="add",
            question_id=p.id,
            old_state=None,
            new_state=p.to_state_dict(),
            created_at=now,
        )
        self.session.add(delta)
        self.session.commit()
        return p, delta

    def delete(self, target) -> Problem:
        p = self._find(target)
        now = self._now()
        old_state = p.to_state_dict()
        qid = p.id
        self.session.delete(p)
        self.session.add(
            Delta(action="delete", question_id=qid, old_state=old_state, new_state=None, created_at=now)
        )
        self.session.commit()
        return p

    def edit_note(self, target, note: str) -> Problem:
        """Update the note only — never reschedules (note editing ≠ review)."""
        p = self._find(target)
        old_state = p.to_state_dict()
        now = self._now()
        p.note = note
        p.updated_at = now
        self.session.flush()
        self.session.add(
            Delta(action="update", question_id=p.id, old_state=old_state, new_state=p.to_state_dict(), created_at=now)
        )
        self.session.commit()
        return p

    def undo(self) -> None:
        last = self.session.scalars(select(Delta).order_by(Delta.id.desc())).first()
        if last is None:
            raise NoActionError("no action to undo")

        current = self.session.get(Problem, last.question_id)
        if current is not None:
            self.session.delete(current)
            self.session.flush()  # ensure the delete lands before re-inserting the same id
        if last.old_state is not None:
            self.session.add(Problem.from_state_dict(last.old_state))
        self.session.delete(last)
        self.session.commit()

    # -- settings --

    def get_setting(self, key: str, default: Any = None) -> Any:
        s = self.session.get(Setting, key)
        return s.value if s is not None else default

    def set_setting(self, key: str, value: Any) -> None:
        s = self.session.get(Setting, key)
        if s is None:
            self.session.add(Setting(key=key, value=value))
        else:
            s.value = value
        self.session.commit()

    # -- helpers --

    def _find(self, target) -> Problem:
        if isinstance(target, int) or (isinstance(target, str) and target.isdigit()):
            p = self.session.get(Problem, int(target))
        else:
            _, url = parse_leetcode_url(target)
            p = self.session.scalar(select(Problem).where(Problem.url == url))
        if p is None:
            raise NotFoundError(f"question not found: {target!r}")
        return p

    @staticmethod
    def _to_question(p: Problem) -> Question:
        return Question(
            id=p.id,
            url=p.url,
            note=p.note,
            familiarity=Familiarity(p.familiarity),
            importance=Importance(p.importance),
            last_reviewed=p.last_reviewed,
            next_review=p.next_review,
            review_count=p.review_count,
            ease_factor=p.ease_factor,
        )

    @staticmethod
    def _apply_schedule(p: Problem, q: Question) -> None:
        p.familiarity = int(q.familiarity)
        p.importance = int(q.importance)
        p.last_reviewed = q.last_reviewed
        p.next_review = q.next_review
        p.review_count = q.review_count
        p.ease_factor = q.ease_factor


def get_setting_value(session: Session, key: str, default: Any = None) -> Any:
    s = session.get(Setting, key)
    return s.value if s is not None else default


def set_setting_value(session: Session, key: str, value: Any) -> None:
    s = session.get(Setting, key)
    if s is None:
        session.add(Setting(key=key, value=value))
    else:
        s.value = value
    session.commit()


def scheduler_from_settings(session: Session) -> Scheduler:
    return Scheduler(
        randomize_interval=bool(get_setting_value(session, "randomize_interval", True)),
        overdue_penalty=bool(get_setting_value(session, "overdue_penalty", False)),
        overdue_limit=int(get_setting_value(session, "overdue_limit", 7)),
    )
