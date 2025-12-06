from sqlalchemy.orm import Session
from .db import TAModel
from .schemas import TA, TACreate, TAUpdate

def list_tas(db: Session):
    rows = db.query(TAModel).all()
    return [TA(ta_id=r.ta_id, ta_name=r.ta_name, email=r.email) for r in rows]

def get_ta(db: Session, ta_id: int):
    r = db.query(TAModel).filter(TAModel.ta_id == ta_id).first()
    if not r:
        return None
    return TA(ta_id=r.ta_id, ta_name=r.ta_name, email=r.email)

def create_ta(db: Session, payload: TACreate):
    exists = db.query(TAModel).filter(TAModel.email == payload.email).first()
    if exists:
        return None
    m = TAModel(ta_name=payload.ta_name, email=payload.email)
    db.add(m)
    db.commit()
    db.refresh(m)
    return TA(ta_id=m.ta_id, ta_name=m.ta_name, email=m.email)

def update_ta(db: Session, ta_id: int, payload: TAUpdate):
    r = db.query(TAModel).filter(TAModel.ta_id == ta_id).first()
    if not r:
        return None
    if payload.ta_name is not None:
        r.ta_name = payload.ta_name
    if payload.email is not None:
        r.email = payload.email
    db.commit()
    db.refresh(r)
    return TA(ta_id=r.ta_id, ta_name=r.ta_name, email=r.email)
