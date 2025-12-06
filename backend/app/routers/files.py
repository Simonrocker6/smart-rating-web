from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..s3 import presign_put
import os
import boto3
from urllib.parse import urlparse

router = APIRouter()

class PresignReq(BaseModel):
    file_name: str
    content_type: str
    exam_id: str | None = None
    test_code: str | None = None

@router.post('/presign')
def api_presign(req: PresignReq):
    try:
        return presign_put(req.file_name, req.content_type, req.exam_id, req.test_code)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="S3 presign failed")

class ViewReq(BaseModel):
    file_url: str

@router.post('/view')
def api_view(req: ViewReq):
    try:
        parsed = urlparse(req.file_url)
        if '.s3' not in parsed.netloc:
            raise HTTPException(status_code=400, detail='Invalid S3 URL')
        bucket = parsed.netloc.split('.s3')[0]
        key = parsed.path.lstrip('/')
        region = os.getenv('AWS_REGION')
        s3 = boto3.client('s3', region_name=region) if region else boto3.client('s3')
        url = s3.generate_presigned_url('get_object', Params={'Bucket': bucket, 'Key': key}, ExpiresIn=int(os.getenv('S3_PRESIGN_EXPIRE', '3600')))
        return {"url": url}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail='S3 view presign failed')
