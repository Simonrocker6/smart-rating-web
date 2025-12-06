import uuid
from sqlalchemy.orm import Session
from .db import PaperModel
from .schemas import Paper, PaperCreate

def list_papers(db: Session, exam_id: str | None = None):
    q = db.query(PaperModel)
    if exam_id:
        q = q.filter(PaperModel.exam_id == exam_id)
    rows = q.all()
    return [Paper(paper_id=r.paper_id, exam_id=r.exam_id, test_code=r.test_code, ta_id=r.ta_id, file_name=r.file_name, file_url=r.file_url, submitted_at=r.submitted_at, questions=r.questions) for r in rows]

def create_paper(db: Session, payload: PaperCreate):
    pid = str(uuid.uuid4())
    m = PaperModel(
        paper_id=pid,
        exam_id=payload.exam_id,
        test_code=payload.test_code,
        ta_id=payload.ta_id,
        file_name=payload.file_name,
        file_url=payload.file_url,
        submitted_at=__import__('datetime').datetime.utcnow().isoformat(),
        questions=[q.dict() for q in payload.questions],
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return Paper(paper_id=m.paper_id, exam_id=m.exam_id, test_code=m.test_code, ta_id=m.ta_id, file_name=m.file_name, file_url=m.file_url, submitted_at=m.submitted_at, questions=m.questions)
