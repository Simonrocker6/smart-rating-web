import os
import time
import uuid
from typing import Optional

def get_s3_bucket() -> Optional[str]:
    env = os.getenv("ENV", "development")
    key_map = {
        "development": "S3_BUCKET_UPLOADS_DEV",
        "test": "S3_BUCKET_UPLOADS_TEST",
        "production": "S3_BUCKET_UPLOADS_PROD",
    }
    return (
        os.getenv(key_map.get(env, "S3_BUCKET_UPLOADS_DEV"))
        or os.getenv("S3_BUCKET_UPLOADS")
        or os.getenv("S3_BUCKET")
    )

def presign_put(file_name: str, content_type: str, exam_id: Optional[str] = None, test_code: Optional[str] = None):
    bucket = get_s3_bucket()
    if not bucket:
        raise RuntimeError("S3 bucket not configured")
    import boto3
    region = os.getenv("AWS_REGION")
    s3 = boto3.client("s3", region_name=region) if region else boto3.client("s3")
    key = _build_key(file_name, exam_id, test_code)
    url = s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": bucket, "Key": key, "ContentType": content_type},
        ExpiresIn=int(os.getenv("S3_PRESIGN_EXPIRE", "3600")),
    )
    return {"url": url, "key": key, "bucket": bucket}

def key_to_url(bucket: str, key: str) -> str:
    return f"https://{bucket}.s3.amazonaws.com/{key}"

def _build_key(file_name: str, exam_id: Optional[str], test_code: Optional[str]) -> str:
    ts = int(time.time())
    uid = uuid.uuid4().hex
    # Store original PDFs under papers/ prefix
    # test_code is not reliable before OCR, so do not include it here
    prefix = f"papers/{exam_id or 'unknown'}"
    return f"{prefix}/{ts}_{uid}_{file_name}"
