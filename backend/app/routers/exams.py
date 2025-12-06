from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import SessionLocal, init_db
from ..schemas import Exam, ExamCreate, ExamUpdate
from ..crud import list_exams, get_exam, create_exam, update_exam, delete_exam

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=list[Exam])
def api_list_exams(db: Session = Depends(get_db)):
    return list_exams(db)

@router.get("/{exam_id}", response_model=Exam)
def api_get_exam(exam_id: str, db: Session = Depends(get_db)):
    r = get_exam(db, exam_id)
    if not r:
        raise HTTPException(status_code=404, detail="Not found")
    return r

@router.post("/", response_model=Exam)
def api_create_exam(payload: ExamCreate, db: Session = Depends(get_db)):
    return create_exam(db, payload)

@router.put("/{exam_id}", response_model=Exam)
def api_update_exam(exam_id: str, payload: ExamUpdate, db: Session = Depends(get_db)):
    r = update_exam(db, exam_id, payload)
    if not r:
        raise HTTPException(status_code=404, detail="Not found")
    return r

@router.delete("/{exam_id}")
def api_delete_exam(exam_id: str, db: Session = Depends(get_db)):
    ok = delete_exam(db, exam_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Not found")
    return {"deleted": True}
