"""Auth primitives: HMAC-signed tokens, GitHub OAuth, and the mentor share link."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets

import httpx


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def sign(payload: dict, secret: str) -> str:
    body = _b64(json.dumps(payload, separators=(",", ":")).encode())
    sig = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def unsign(token: str, secret: str) -> dict | None:
    try:
        body, sig = token.split(".", 1)
    except ValueError:
        return None
    expected = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return None
    try:
        return json.loads(_unb64(body))
    except Exception:
        return None


def create_session_token(github_id, login: str, secret: str) -> str:
    return sign({"github_id": github_id, "login": login}, secret)


def new_share_token() -> str:
    return secrets.token_urlsafe(24)


def github_authorize_url(client_id: str, redirect_uri: str) -> str:
    state = secrets.token_urlsafe(16)
    params = f"client_id={client_id}&redirect_uri={redirect_uri}&scope=read:user&state={state}"
    return f"https://github.com/login/oauth/authorize?{params}"


async def exchange_code(client_id: str, client_secret: str, code: str) -> dict:
    """Exchange an OAuth authorization code for a GitHub user (id, login)."""
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            data={"client_id": client_id, "client_secret": client_secret, "code": code},
            headers={"Accept": "application/json"},
        )
        token_resp.raise_for_status()
        access_token = token_resp.json().get("access_token")
        if not access_token:
            raise ValueError("no access token")
        user_resp = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        user_resp.raise_for_status()
        user = user_resp.json()
        return {"github_id": user["id"], "login": user["login"]}


def get_share_token(db) -> str | None:
    from app.service import get_setting_value

    v = get_setting_value(db, "share_token", None)
    return v if v else None


def ensure_share_token(db) -> str:
    from app.service import get_setting_value, set_setting_value

    token = get_setting_value(db, "share_token", None)
    if not token:
        token = new_share_token()
        set_setting_value(db, "share_token", token)
    return token


def upsert_owner(db, user: dict) -> None:
    from app.models import Owner
    from app.service import now_utc

    o = db.get(Owner, 1)
    if o is None:
        o = Owner(id=1, github_id=user["github_id"], github_login=user["login"], created_at=now_utc())
        db.add(o)
    else:
        o.github_id = user["github_id"]
        o.github_login = user["login"]
    db.commit()
