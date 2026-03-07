from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select, or_
from ...database import get_session
from ...models.algorithm import Algorithm

router = APIRouter()


@router.get("/")
async def search_algorithms(
    q: str = Query(..., min_length=1),
    session: Session = Depends(get_session),
):
    # Phase 1: simple text search on name, description, best_use_case
    # Phase 4: replace with pgvector semantic search
    term = f"%{q}%"
    algorithms = session.exec(
        select(Algorithm).where(
            or_(
                Algorithm.name.ilike(term),
                Algorithm.description.ilike(term),
                Algorithm.best_use_case.ilike(term),
                Algorithm.author.ilike(term),
            )
        )
    ).all()
    return {"data": algorithms, "meta": {"total": len(algorithms), "query": q}}
