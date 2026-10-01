"""Settings read/update endpoints."""

from fastapi import APIRouter, Depends

from app.deps import get_service, require_owner, require_read
from app.schemas import SettingsIn, SettingsOut

router = APIRouter(prefix="/api/settings", tags=["settings"], dependencies=[Depends(require_read)])


def _read(service) -> SettingsOut:
    return SettingsOut(
        randomize_interval=service.get_setting("randomize_interval", True),
        overdue_penalty=service.get_setting("overdue_penalty", False),
        overdue_limit=service.get_setting("overdue_limit", 7),
        top_k_due=service.get_setting("top_k_due", 10),
        top_k_upcoming=service.get_setting("top_k_upcoming", 10),
    )


@router.get("", response_model=SettingsOut)
def get_settings(service=Depends(get_service)):
    return _read(service)


@router.put("", response_model=SettingsOut, dependencies=[Depends(require_owner)])
def update_settings(body: SettingsIn, service=Depends(get_service)):
    if body.randomize_interval is not None:
        service.set_setting("randomize_interval", body.randomize_interval)
    if body.overdue_penalty is not None:
        service.set_setting("overdue_penalty", body.overdue_penalty)
    if body.overdue_limit is not None:
        service.set_setting("overdue_limit", body.overdue_limit)
    if body.top_k_due is not None:
        service.set_setting("top_k_due", body.top_k_due)
    if body.top_k_upcoming is not None:
        service.set_setting("top_k_upcoming", body.top_k_upcoming)
    return _read(service)
