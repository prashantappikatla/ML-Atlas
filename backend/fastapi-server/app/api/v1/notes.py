from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from ...database import get_session
from ...models.algorithm import AlgorithmNote

router = APIRouter()


@router.get("/{algorithm_id}")
async def get_notes(algorithm_id: int, session: Session = Depends(get_session)):
    notes = session.exec(
        select(AlgorithmNote).where(AlgorithmNote.algorithm_id == algorithm_id)
    ).all()
    return {"data": notes}


@router.post("/")
async def create_note(note: AlgorithmNote, session: Session = Depends(get_session)):
    from datetime import datetime, timezone
    note.created_at = datetime.now(timezone.utc).isoformat()
    session.add(note)
    session.commit()
    session.refresh(note)
    return {"data": note}


@router.put("/{note_id}")
async def update_note(
    note_id: int,
    updated: AlgorithmNote,
    session: Session = Depends(get_session),
):
    note = session.get(AlgorithmNote, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    note.content = updated.content
    note.note_type = updated.note_type
    session.commit()
    session.refresh(note)
    return {"data": note}
