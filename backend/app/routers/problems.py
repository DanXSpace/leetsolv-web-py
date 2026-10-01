"""Problem CRUD, review, undo, history, status, and search endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Response

from app.deps import get_service, require_owner, require_read
from app.scheduler import Familiarity, Importance, MemoryUse
from app.schemas import DeltaOut, NoteIn, ProblemOut, ReviewIn, StatusOut, UpsertIn
from app.service import NoActionError, NotFoundError
from app.urls import UrlError

router = APIRouter(prefix="/api", tags=["problems"], dependencies=[Depends(require_read)])


def _to_enums(body) -> tuple[Familiarity, Importance, MemoryUse]:
    fam = Familiarity(body.familiarity)
    imp = Importance(body.importance)
    # leetsolv only asks for memory when familiarity >= Medium; otherwise Reasoned.
    mem = MemoryUse(body.memory) if fam >= Familiarity.MEDIUM else MemoryUse.REASONED
    return fam, imp, mem


@router.get("/problems", response_model=list[ProblemOut])
def list_problems(service=Depends(get_service)):
    return service.list_all()


@router.get("/problems/{target}", response_model=ProblemOut)
def get_problem(target: str, service=Depends(get_service)):
    try:
        return service.get(target)
    except (NotFoundError, UrlError):
        raise HTTPException(status_code=404, detail="question not found")


@router.post("/problems", response_model=ProblemOut, status_code=201, dependencies=[Depends(require_owner)])
def add_problem(body: UpsertIn, service=Depends(get_service)):
    fam, imp, mem = _to_enums(body)
    try:
        problem, _ = service.upsert(body.url, body.note, fam, imp, mem)
    except UrlError:
        raise HTTPException(status_code=400, detail="invalid LeetCode URL")
    return problem


@router.post("/review", response_model=ProblemOut, dependencies=[Depends(require_owner)])
def review(body: ReviewIn, service=Depends(get_service)):
    try:
        existing = service.get(body.target)
    except (NotFoundError, UrlError):
        raise HTTPException(status_code=404, detail="question not found")
    fam, imp, mem = _to_enums(body)
    # Note is preserved on review — editing a note is a separate action.
    updated, _ = service.upsert(existing.url, existing.note, fam, imp, mem)
    return updated


@router.patch("/problems/{target}/note", response_model=ProblemOut, dependencies=[Depends(require_owner)])
def edit_note(target: str, body: NoteIn, service=Depends(get_service)):
    try:
        return service.edit_note(target, body.note)
    except (NotFoundError, UrlError):
        raise HTTPException(status_code=404, detail="question not found")


@router.delete("/problems/{target}", status_code=204, dependencies=[Depends(require_owner)])
def delete_problem(target: str, service=Depends(get_service)):
    try:
        service.delete(target)
    except (NotFoundError, UrlError):
        raise HTTPException(status_code=404, detail="question not found")
    return Response(status_code=204)


@router.post("/undo", status_code=204, dependencies=[Depends(require_owner)])
def undo(service=Depends(get_service)):
    try:
        service.undo()
    except NoActionError:
        raise HTTPException(status_code=400, detail="nothing to undo")
    return Response(status_code=204)


@router.get("/history", response_model=list[DeltaOut])
def history(service=Depends(get_service)):
    return service.history()


@router.get("/status", response_model=StatusOut)
def status(service=Depends(get_service)):
    return service.status_summary()


@router.get("/search", response_model=list[ProblemOut])
def search(
    query: str | None = None,
    familiarity: int | None = None,
    importance: int | None = None,
    review_count: int | None = None,
    due_only: bool = False,
    service=Depends(get_service),
):
    return service.search(
        query=query,
        familiarity=familiarity,
        importance=importance,
        review_count=review_count,
        due_only=due_only,
    )
