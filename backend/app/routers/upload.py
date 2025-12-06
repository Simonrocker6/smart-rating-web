from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from ..db import SessionLocal, init_db, PaperModel
import os, time, uuid
import boto3
from urllib.parse import quote

router = APIRouter()

def get_db():
    init_db()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _get_bucket():
    bucket = os.getenv('S3_BUCKET_UPLOADS_PROD') or os.getenv('S3_BUCKET_UPLOADS') or os.getenv('S3_BUCKET')
    if not bucket:
        raise HTTPException(status_code=400, detail='S3 bucket not configured')
    return bucket

@router.post('/paper')
async def upload_paper(
    exam_id: str = Form(...),
    ta_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    bucket = _get_bucket()
    region = os.getenv('AWS_REGION')
    s3 = boto3.client('s3', region_name=region) if region else boto3.client('s3')
    ts = int(time.time())
    uid = uuid.uuid4().hex
    safe_name = quote(file.filename)
    key = f"papers/{exam_id}/{ts}_{uid}_{safe_name}"
    try:
        # stream upload
        s3.upload_fileobj(file.file, bucket, key, ExtraArgs={'ContentType': file.content_type or 'application/octet-stream'})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Upload failed: {type(e).__name__}')
    file_url = f"https://{bucket}.s3.amazonaws.com/{key}"
    paper_id = str(uuid.uuid4())
    m = PaperModel(
        paper_id=paper_id,
        exam_id=exam_id,
        test_code='UNKNOWN',
        ta_id=ta_id,
        file_name=file.filename,
        file_url=file_url,
        submitted_at=__import__('datetime').datetime.utcnow().isoformat(),
        questions=[]
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return {
        'paper_id': m.paper_id,
        'exam_id': m.exam_id,
        'test_code': m.test_code,
        'ta_id': m.ta_id,
        'file_name': m.file_name,
        'file_url': m.file_url,
        'submitted_at': m.submitted_at,
        'questions': m.questions
    }
