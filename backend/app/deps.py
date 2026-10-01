"""FastAPI dependencies: DB session, service, and the auth principal."""

from __future__ import annotations

import hmac

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.auth import get_share_token, unsign
from app.db import SessionLocal
from app.service import QuestionService, get_setting_value, scheduler_from_settings


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_service(db: Session = Depends(get_db)) -> QuestionService:
    return QuestionService(
        db,
        scheduler_from_settings(db),
        top_k_due=int(get_setting_value(db, "top_k_due", 10)),
        top_k_upcoming=int(get_setting_value(db, "top_k_upcoming", 10)),
    )


def get_principal(request: Request, db: Session = Depends(get_db)) -> str | None:
    cfg = request.app.state.settings
    token = request.cookies.get("leetsolv_session")
    if token:
        payload = unsign(token, cfg.secret_key)
        if payload and str(payload.get("github_id")) == str(cfg.owner_github_id):
            return "owner"
    share = request.headers.get("X-Share-Token") or request.query_params.get("share")
    if share:
        stored = get_share_token(db)
        if stored and hmac.compare_digest(share, stored):
            return "mentor"
    return None


def require_owner(principal: str | None = Depends(get_principal)) -> None:
    if principal != "owner":
        raise HTTPException(status_code=403, detail="owner only")


def require_read(principal: str | None = Depends(get_principal)) -> None:
    if principal not in ("owner", "mentor"):
        raise HTTPException(status_code=401, detail="authentication required")
