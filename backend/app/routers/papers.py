from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from ..db import SessionLocal, init_db
from ..schemas import Paper, PaperCreate
from ..crud_paper import list_papers, create_paper

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get('/', response_model=list[Paper])
def api_list_papers(exam_id: Optional[str] = None, db: Session = Depends(get_db)):
    return list_papers(db, exam_id)

@router.post('/', response_model=Paper)
def api_create_paper(payload: PaperCreate, db: Session = Depends(get_db)):
    return create_paper(db, payload)
