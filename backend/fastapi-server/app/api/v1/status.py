from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func
from ...database import get_session
from ...models.status import ImplementationStatus
from ...models.algorithm import Algorithm

router = APIRouter()


@router.get("/")
async def list_status(session: Session = Depends(get_session)):
    statuses = session.exec(select(ImplementationStatus)).all()

    # Compute summary counts
    counts: dict[str, int] = {}
    for s in statuses:
        counts[s.status] = counts.get(s.status, 0) + 1

    # Compute by-category counts
    by_category: dict[str, dict] = {}
    results = session.exec(
        select(Algorithm.category, ImplementationStatus.status, func.count())
        .join(ImplementationStatus, Algorithm.id == ImplementationStatus.algorithm_id)
        .group_by(Algorithm.category, ImplementationStatus.status)
    ).all()
    for category, status, count in results:
        if category not in by_category:
            by_category[category] = {"total": 0}
        by_category[category]["total"] += count
        by_category[category][status] = count

    return {
        "data": {
            "summary": {"total": len(statuses), **counts},
            "by_category": by_category,
        }
    }


@router.get("/{algorithm_id}")
async def get_status(algorithm_id: int, session: Session = Depends(get_session)):
    status = session.exec(
        select(ImplementationStatus).where(ImplementationStatus.algorithm_id == algorithm_id)
    ).first()
    if not status:
        raise HTTPException(status_code=404, detail="Status not found")
    return {"data": status}


@router.put("/{algorithm_id}")
async def update_status(
    algorithm_id: int,
    updated: ImplementationStatus,
    session: Session = Depends(get_session),
):
    from datetime import datetime, timezone
    status = session.exec(
        select(ImplementationStatus).where(ImplementationStatus.algorithm_id == algorithm_id)
    ).first()
    if not status:
        raise HTTPException(status_code=404, detail="Status not found")

    for field in ["status", "implemented_from_scratch", "implemented_library",
                  "lab_created", "documentation_complete", "notes_added"]:
        setattr(status, field, getattr(updated, field))
    status.last_updated = datetime.now(timezone.utc).isoformat()

    session.commit()
    session.refresh(status)
    return {"data": status}
