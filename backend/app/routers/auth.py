"""Auth endpoints: GitHub OAuth login, current user, and the mentor share link."""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth import (
    create_session_token,
    ensure_share_token,
    exchange_code,
    github_authorize_url,
    new_share_token,
    unsign,
    upsert_owner,
)
from app.deps import get_db, get_principal, require_owner
from app.schemas import MeOut, ShareOut
from app.service import set_setting_value

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/me", response_model=MeOut)
def me(request: Request, principal: str | None = Depends(get_principal)):
    if principal == "owner":
        token = request.cookies.get("leetsolv_session")
        payload = unsign(token, request.app.state.settings.secret_key) if token else None
        return MeOut(role="owner", github_login=payload.get("login") if payload else None)
    return MeOut(role=principal or "anonymous")


@router.get("/login")
def login(request: Request):
    cfg = request.app.state.settings
    redirect_uri = f"{cfg.base_url}/api/auth/callback"
    return {"authorize_url": github_authorize_url(cfg.github_client_id, redirect_uri)}


@router.get("/callback")
async def callback(request: Request, code: str, db: Session = Depends(get_db)):
    cfg = request.app.state.settings
    try:
        user = await exchange_code(cfg.github_client_id, cfg.github_client_secret, code)
    except Exception:
        raise HTTPException(status_code=400, detail="GitHub authentication failed")
    if str(user["github_id"]) != str(cfg.owner_github_id):
        raise HTTPException(status_code=403, detail="GitHub account is not the app owner")
    upsert_owner(db, user)
    token = create_session_token(user["github_id"], user["login"], cfg.secret_key)
    resp = RedirectResponse(url=cfg.base_url, status_code=302)
    resp.set_cookie("leetsolv_session", token, httponly=True, samesite="lax", max_age=60 * 60 * 24 * 30)
    return resp


@router.post("/logout")
def logout(request: Request):
    resp = RedirectResponse(url=request.app.state.settings.base_url, status_code=302)
    resp.delete_cookie("leetsolv_session")
    return resp


@router.get("/share", response_model=ShareOut, dependencies=[Depends(require_owner)])
def share(request: Request, db: Session = Depends(get_db)):
    token = ensure_share_token(db)
    return ShareOut(token=token, url=f"{request.app.state.settings.base_url}/share/{token}")


@router.post("/share/reset", response_model=ShareOut, dependencies=[Depends(require_owner)])
def share_reset(request: Request, db: Session = Depends(get_db)):
    token = new_share_token()
    set_setting_value(db, "share_token", token)
    return ShareOut(token=token, url=f"{request.app.state.settings.base_url}/share/{token}")
