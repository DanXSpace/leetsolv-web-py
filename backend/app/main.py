"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, settings
from app.db import init_db
from app.routers import auth as auth_router
from app.routers import problems as problems_router
from app.routers import settings as settings_router


def create_app(cfg: Settings | None = None, *, init_db_: bool = True) -> FastAPI:
    cfg = cfg or settings
    if init_db_:
        init_db()

    app = FastAPI(title="leetsolv-web")
    app.state.settings = cfg
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(problems_router.router)
    app.include_router(settings_router.router)
    app.include_router(auth_router.router)

    @app.get("/api/health")
    def health():
        return {"ok": True}

    return app


app = create_app()
