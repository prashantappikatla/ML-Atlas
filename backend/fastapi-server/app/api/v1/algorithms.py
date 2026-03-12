from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select
from ...database import get_session
from ...models.algorithm import Algorithm
from ...models.status import ImplementationStatus

router = APIRouter()


@router.get("/")
async def list_algorithms(
    category: str | None = Query(None),
    subcategory: str | None = Query(None),
    status: str | None = Query(None),
    complexity: str | None = Query(None),
    session: Session = Depends(get_session),
):
    query = select(Algorithm)
    if category:
        query = query.where(Algorithm.category == category)
    if subcategory:
        query = query.where(Algorithm.subcategory == subcategory)
    if complexity:
        query = query.where(Algorithm.complexity == complexity)
    if status:
        query = query.join(
            ImplementationStatus,
            Algorithm.id == ImplementationStatus.algorithm_id,
        ).where(ImplementationStatus.status == status)

    algorithms = session.exec(query).all()

    # Batch-fetch statuses to include in every response object (avoids N+1)
    algo_ids = [a.id for a in algorithms]
    status_map: dict[int, str] = {}
    if algo_ids:
        rows = session.exec(
            select(ImplementationStatus).where(
                ImplementationStatus.algorithm_id.in_(algo_ids)
            )
        ).all()
        status_map = {r.algorithm_id: r.status for r in rows}

    data = [
        {**a.model_dump(), "status": status_map.get(a.id, "planned")}
        for a in algorithms
    ]
    return {"data": data, "meta": {"total": len(data)}}


@router.get("/by-slug/{slug}")
async def get_algorithm_by_slug(slug: str, session: Session = Depends(get_session)):
    algorithm = session.exec(select(Algorithm).where(Algorithm.slug == slug)).first()
    if not algorithm:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Algorithm not found")
    return {"data": algorithm}


@router.get("/{algorithm_id}")
async def get_algorithm(algorithm_id: int, session: Session = Depends(get_session)):
    algorithm = session.get(Algorithm, algorithm_id)
    if not algorithm:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Algorithm not found")
    return {"data": algorithm}
