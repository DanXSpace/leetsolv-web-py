"""Runtime configuration from environment variables."""

from __future__ import annotations

import os
import secrets


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


class Settings:
    def __init__(self) -> None:
        self.secret_key = _env("LEETSOLV_SECRET_KEY") or secrets.token_hex(32)
        self.github_client_id = _env("LEETSOLV_GITHUB_CLIENT_ID")
        self.github_client_secret = _env("LEETSOLV_GITHUB_CLIENT_SECRET")
        # The single GitHub account allowed to log in as owner.
        self.owner_github_id = _env("LEETSOLV_OWNER_GITHUB_ID")
        # Public origin of the app (frontend + API share an origin in prod).
        self.base_url = _env("LEETSOLV_BASE_URL", "http://localhost:5173")
        self.cors_origins = [
            o.strip()
            for o in _env("LEETSOLV_CORS_ORIGINS", "http://localhost:5173").split(",")
            if o.strip()
        ]


settings = Settings()
