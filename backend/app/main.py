"""FastAPI application factory."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import Settings, settings
from app.db import init_db
from app.routers import auth as auth_router
from app.routers import problems as problems_router
from app.routers import settings as settings_router


def _mount_spa(app: FastAPI, dist_dir: str) -> None:
    """Serve the built frontend when it's available.

    Registers the ``/assets`` static mount and a catch-all that returns
    ``index.html`` for any non-API GET, so BrowserRouter deep links (e.g.
    ``/share/<token>``) resolve. API routes are registered first and win.
    """
    dist = Path(dist_dir)
    index = dist / "index.html"
    if not index.is_file():
        return

    assets = dist / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="not found")
        return FileResponse(index)


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

    if cfg.dist_dir:
        _mount_spa(app, cfg.dist_dir)

    return app


app = create_app()
