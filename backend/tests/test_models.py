"""Tests for the SQLAlchemy data model."""

import json
from datetime import date, datetime

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models import Delta, Owner, Problem, Setting


@pytest.fixture
def session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with Session() as s:
        yield s


def _problem(**overrides):
    now = datetime(2026, 10, 1, 12, 0, 0)
    data = dict(
        url="https://leetcode.com/problems/two-sum/",
        slug="two-sum",
        note="hash map",
        familiarity=1,
        importance=2,
        last_reviewed=date(2026, 10, 1),
        next_review=date(2026, 10, 6),
        review_count=1,
        ease_factor=1.8,
        created_at=now,
        updated_at=now,
        title="Two Sum",
        difficulty="Easy",
        tags=["array", "hash-table"],
    )
    data.update(overrides)
    return Problem(**data)


def test_problem_has_leetsolv_fields():
    cols = {c.name for c in Problem.__table__.columns}
    assert {
        "url", "note", "familiarity", "importance", "last_reviewed",
        "next_review", "review_count", "ease_factor",
    } <= cols


def test_problem_roundtrip(session):
    p = _problem()
    session.add(p)
    session.commit()
    got = session.scalar(select(Problem).where(Problem.url == p.url))
    assert got is not None
    assert got.slug == "two-sum"
    assert got.familiarity == 1
    assert got.importance == 2
    assert got.ease_factor == 1.8
    assert got.title == "Two Sum"
    assert got.tags == ["array", "hash-table"]


def test_problem_url_unique(session):
    session.add(_problem())
    session.commit()
    with pytest.raises(IntegrityError):
        session.add(_problem())
        session.commit()


def test_delta_json_roundtrip(session):
    d = Delta(
        action="update",
        question_id=7,
        old_state={"ease_factor": 1.8, "familiarity": 1},
        new_state={"ease_factor": 2.0, "familiarity": 2},
        created_at=datetime(2026, 10, 1, 12, 0, 0),
    )
    session.add(d)
    session.commit()
    got = session.scalar(select(Delta).where(Delta.question_id == 7))
    assert got.action == "update"
    assert got.old_state == {"ease_factor": 1.8, "familiarity": 1}
    assert got.new_state == {"ease_factor": 2.0, "familiarity": 2}


def test_setting_roundtrip(session):
    session.add(Setting(key="overdue_limit", value=7))
    session.add(Setting(key="randomize_interval", value=True))
    session.commit()
    assert session.scalar(select(Setting).where(Setting.key == "overdue_limit")).value == 7
    assert session.scalar(select(Setting).where(Setting.key == "randomize_interval")).value is True


def test_owner_single_row(session):
    o = Owner(id=1, github_id=123, github_login="dholun", created_at=datetime(2026, 10, 1, 12, 0, 0))
    session.add(o)
    session.commit()
    got = session.get(Owner, 1)
    assert got.github_login == "dholun"


def test_to_state_dict_json_safe(session):
    p = _problem()
    session.add(p)
    session.commit()
    d = p.to_state_dict()
    assert d["id"] == 1
    assert d["slug"] == "two-sum"
    assert d["last_reviewed"] == "2026-10-01"
    assert d["next_review"] == "2026-10-06"
    assert d["tags"] == ["array", "hash-table"]
    json.dumps(d)  # must not raise
