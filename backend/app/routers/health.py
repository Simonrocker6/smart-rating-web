from fastapi import APIRouter
from sqlalchemy import text
from ..db import engine
from ..config import get_database_url

router = APIRouter()

@router.get("/")
def health():
    url = get_database_url()
    driver = engine.url.drivername
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        status = "ok"
    except Exception as e:
        status = f"error: {type(e).__name__}"
    return {"status": status, "db_driver": driver, "using_url": url.split("@")[0]}
