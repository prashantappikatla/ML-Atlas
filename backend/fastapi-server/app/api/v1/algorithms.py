from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select
from ...database import get_session
from ...models.algorithm import Algorithm

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
    algorithms = session.exec(query).all()
    return {"data": algorithms, "meta": {"total": len(algorithms)}}


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
