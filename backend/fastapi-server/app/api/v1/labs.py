from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from ...database import get_session
from ...models.lab import Lab
from ...models.algorithm import Algorithm

router = APIRouter()


@router.get("/")
async def list_labs(session: Session = Depends(get_session)):
    labs = session.exec(select(Lab)).all()
    return {"data": labs, "meta": {"total": len(labs)}}


@router.get("/{algorithm_slug}")
async def get_lab_by_algorithm(algorithm_slug: str, session: Session = Depends(get_session)):
    algorithm = session.exec(
        select(Algorithm).where(Algorithm.slug == algorithm_slug)
    ).first()
    if not algorithm:
        raise HTTPException(status_code=404, detail="Algorithm not found")
    lab = session.exec(select(Lab).where(Lab.algorithm_id == algorithm.id)).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found for this algorithm")
    return {"data": lab}


@router.post("/")
async def create_lab(lab: Lab, session: Session = Depends(get_session)):
    session.add(lab)
    session.commit()
    session.refresh(lab)
    return {"data": lab}
