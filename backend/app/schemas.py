"""Pydantic request/response schemas for the API."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ProblemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    slug: str
    note: str
    familiarity: int  # 0..4
    importance: int  # 0..3
    last_reviewed: date | None
    next_review: date | None
    review_count: int
    ease_factor: float
    title: str | None
    difficulty: str | None
    tags: list[str] | None
    created_at: datetime
    updated_at: datetime


class UpsertIn(BaseModel):
    url: str
    note: str = ""
    familiarity: int = Field(ge=0, le=4)
    importance: int = Field(ge=0, le=3)
    memory: int = Field(default=0, ge=0, le=2)


class ReviewIn(BaseModel):
    target: str  # row id, or a LeetCode URL
    familiarity: int = Field(ge=0, le=4)
    importance: int = Field(ge=0, le=3)
    memory: int = Field(default=0, ge=0, le=2)


class NoteIn(BaseModel):
    note: str


class DeltaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action: str
    question_id: int
    old_state: dict | None
    new_state: dict | None
    created_at: datetime


class StatusOut(BaseModel):
    total: int
    total_due: int
    total_upcoming: int
    due: list[ProblemOut]
    upcoming: list[ProblemOut]


class SettingsOut(BaseModel):
    randomize_interval: bool
    overdue_penalty: bool
    overdue_limit: int
    top_k_due: int
    top_k_upcoming: int


class SettingsIn(BaseModel):
    randomize_interval: bool | None = None
    overdue_penalty: bool | None = None
    overdue_limit: int | None = Field(default=None, ge=1, le=90)
    top_k_due: int | None = Field(default=None, ge=1, le=100)
    top_k_upcoming: int | None = Field(default=None, ge=1, le=100)


class MeOut(BaseModel):
    role: str
    github_login: str | None = None


class ShareOut(BaseModel):
    token: str
    url: str
