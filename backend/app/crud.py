import uuid
from sqlalchemy.orm import Session
from .db import ExamModel
from .schemas import Exam, ExamCreate, ExamUpdate

def list_exams(db: Session):
    rows = db.query(ExamModel).all()
    def qlist(r):
        root = getattr(r, 'rubrics', None) or {}
        return root.get("questions", [])
    return [Exam(exam_id=r.exam_id, title=r.title, total_questions=r.total_questions, created_at=r.created_at, questions=qlist(r), total_images=r.total_images) for r in rows]

def get_exam(db: Session, exam_id: str):
    r = db.query(ExamModel).filter(ExamModel.exam_id == exam_id).first()
    if not r:
        return None
    root = getattr(r, 'rubrics', None) or {}
    return Exam(exam_id=r.exam_id, title=r.title, total_questions=r.total_questions, created_at=r.created_at, questions=root.get("questions", []), total_images=r.total_images)

def create_exam(db: Session, payload: ExamCreate):
    eid = str(uuid.uuid4())
    model = ExamModel(
        exam_id=eid,
        title=payload.title,
        total_questions=payload.total_questions,
        created_at=payload.created_at,
        rubrics={"questions": [q.dict() for q in payload.questions]},
        total_images=payload.total_images if payload.total_images is not None else (2 * len(payload.questions) + 1),
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    return get_exam(db, eid)

def update_exam(db: Session, exam_id: str, payload: ExamUpdate):
    r = db.query(ExamModel).filter(ExamModel.exam_id == exam_id).first()
    if not r:
        return None
    if payload.title is not None:
        r.title = payload.title
    if payload.total_questions is not None:
        r.total_questions = payload.total_questions
    if payload.created_at is not None:
        r.created_at = payload.created_at
    if payload.questions is not None:
        r.rubrics = {"questions": [q.dict() for q in payload.questions]}
        if r.total_images is None:
            r.total_images = 2 * len(payload.questions) + 1
    if payload.total_images is not None:
        r.total_images = payload.total_images
    db.commit()
    db.refresh(r)
    return get_exam(db, exam_id)

def delete_exam(db: Session, exam_id: str) -> bool:
    r = db.query(ExamModel).filter(ExamModel.exam_id == exam_id).first()
    if not r:
        return False
    db.delete(r)
    db.commit()
    return True
