from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import SessionLocal, init_db
from ..schemas import TA, TACreate, TAUpdate
from ..crud_ta import list_tas, get_ta, create_ta, update_ta

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=list[TA])
def api_list_tas(db: Session = Depends(get_db)):
    return list_tas(db)

@router.get("/{ta_id}", response_model=TA)
def api_get_ta(ta_id: int, db: Session = Depends(get_db)):
    r = get_ta(db, ta_id)
    if not r:
        raise HTTPException(status_code=404, detail="Not found")
    return r

@router.post("/", response_model=TA)
def api_create_ta(payload: TACreate, db: Session = Depends(get_db)):
    r = create_ta(db, payload)
    if not r:
        raise HTTPException(status_code=409, detail="Email exists")
    return r

@router.put("/{ta_id}", response_model=TA)
def api_update_ta(ta_id: int, payload: TAUpdate, db: Session = Depends(get_db)):
    r = update_ta(db, ta_id, payload)
    if not r:
        raise HTTPException(status_code=404, detail="Not found")
    return r
