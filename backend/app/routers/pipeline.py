from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from ..db import SessionLocal, init_db, PaperModel, ExamModel
import os, time, uuid, threading
import boto3
from urllib.parse import quote
from .process import api_segment, api_ocr, api_grade
import tempfile
import cv2
import base64
import os
from pdf2image import convert_from_path
import numpy as np
import botocore
from typing import Optional, Dict, Any
import json
import requests
import random

router = APIRouter()

def get_db():
    init_db()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

JOBS: dict[str, dict] = {}
LOCK = threading.Lock()

# Mathpix headers resolved from environment if present
headers = {
    "app_id": os.getenv("MATHPIX_APP_ID", ""),
    "app_key": os.getenv("MATHPIX_APP_KEY", ""),
    "Content-Type": "application/x-www-form-urlencoded"
}

def bucket():
    b = os.getenv('S3_BUCKET_UPLOADS_PROD') or os.getenv('S3_BUCKET_UPLOADS') or os.getenv('S3_BUCKET')
    if not b:
        raise HTTPException(status_code=400, detail='S3 bucket not configured')
    return b

def _update_job(job_id: str, **kwargs):
    with LOCK:
        JOBS[job_id] = {**JOBS.get(job_id, {}), **kwargs}

def _run_pipeline(job_id: str, paper_id: str):
    _update_job(job_id, status='segmenting')
    try:
        api_segment(paper_id, next(get_db()))
    except Exception as e:
        _update_job(job_id, status='error', error='SEGMENT_ERROR')
        return
    _update_job(job_id, status='ocr')
    try:
        api_ocr(paper_id, next(get_db()))
    except Exception:
        _update_job(job_id, status='error', error='OCR_ERROR')
        return
    _update_job(job_id, status='grading')
    try:
        api_grade(paper_id, next(get_db()))
    except Exception:
        _update_job(job_id, status='error', error='GRADE_ERROR')
        return
    _update_job(job_id, status='done')

@router.post('/run')
async def pipeline_run(
    exam_id: str = Form(...),
    ta_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    b = bucket()
    region = os.getenv('AWS_REGION')
    s3 = boto3.client('s3', region_name=region) if region else boto3.client('s3')
    ts = int(time.time())
    uid = uuid.uuid4().hex
    safe_name = quote(file.filename)
    key = f"papers/{exam_id}/{ts}_{uid}_{safe_name}"
    try:
        s3.upload_fileobj(file.file, b, key, ExtraArgs={'ContentType': file.content_type or 'application/pdf'})
    except Exception:
        raise HTTPException(status_code=500, detail='Upload failed')
    file_url = f"https://{b}.s3.amazonaws.com/{key}"
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
    job_id = uuid.uuid4().hex
    _update_job(job_id, status='queued', paper_id=paper_id)
    threading.Thread(target=_run_pipeline, args=(job_id, paper_id), daemon=True).start()
    return {"job_id": job_id, "paper_id": paper_id}

@router.get('/status')
def pipeline_status(job_id: str):
    with LOCK:
        info = JOBS.get(job_id)
    if not info:
        raise HTTPException(status_code=404, detail='Job not found')
    return info


@router.post('/execute_file')
async def pipeline_execute_file(file: UploadFile = File(...)):
    print(f"API invoked")
    print(f"file.filename: {file.filename}")

    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
        print(f"Created temporary file: {tmp_path}")

    try:
        pages = convert_pdf_to_images(tmp_path, dpi=200)
        print(f"Converted PDF to {len(pages)} pages")

        all_question_b64 = []  # 存放 Base64 图像
        total_questions = 0

        for page_num, page in enumerate(pages, 1):
            print(f"正在处理第 {page_num} 页")
            images = extract_questions(page)
            print(f"第 {page_num} 页有 {len(images)} 个问题")
            for q_num, image_data in enumerate(images, 1):
                total_questions += 1
                # 提取图像 ndarray
                img_array = image_data['image']  # 这是 np.ndarray (BGR)

                # 转为 Base64
                b64_str = image_to_base64(img_array)
                all_question_b64.append({
                    "page": page_num,
                    "question_index": q_num,
                    "image_base64": b64_str  # 可直接在 Apifox 预览
                })

        
        # debug_view.html 生成器（运行一次即可）
        # with open("debug_view.html", "w") as f:

        #     f.write("<html><body>\n")
        #     for item in all_question_b64:
        #         f.write(f'<img src="data:image/png;base64,{item["image_base64"]}" style="max-width:600px"><br>\n')
        #     f.write("</body></html>")


        # 开始OCR的过程

        problem_config_str = '''{
            "images_total": 8,
            "problems":
            [
                {
                    "solution" : 3,
                    "final_answer" : 3
                    },
                {
                    "solution" : 4,
                    "final_answer" : 4
                    },
                {
                    "solution" : 5,
                    "final_answer" : 5
                    },
                    
                {
                    "solution" : 7,
                    "final_answer" : 8
                    }
            ]
        }'''

        problem_config = json.loads(problem_config_str)

        images_set = set()
        for problem in problem_config['problems']:
            images_set.add(problem['solution'])
            images_set.add(problem['final_answer'])
        
        ocr_rlt = {}
        for index in images_set:
            if index > len(all_question_b64):
                raise HTTPException(status_code=400, detail=f"Image index {index} out of range")
            ocr_rlt[index] = upload_image_base64_to_mathpix(all_question_b64[index - 1]['image_base64'])
        
        # AI Grading ..








        return {
            "filename": file.filename,
            "pages": len(pages),
            "total_questions": total_questions,
            "status": "success",
        }

    finally:
        os.unlink(tmp_path)

@router.post('/execute')
async def pipeline_execute(
    exam_id: str = Form(...),
    ta_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    #log exam_id, ta_id, file.filename
    r = db.query(ExamModel).filter(ExamModel.exam_id == exam_id).first()
    if not r:
        raise HTTPException(status_code=201, detail='exam not found')
    total_images = r.total_images

    print(f"exam_id: {exam_id}, ta_id: {ta_id}, file.filename: {file.filename}, total_images: {total_images}")

    # 上传paper到S3
    b = bucket()
    region = os.getenv('AWS_REGION')
    s3 = boto3.client('s3', region_name=region) if region else boto3.client('s3')
    ts = int(time.time())
    uid = uuid.uuid4().hex
    safe_name = quote(file.filename)
    key = f"papers/{exam_id}/{ts}_{uid}_{safe_name}"
    try:
        s3.upload_fileobj(file.file, b, key, ExtraArgs={'ContentType': file.content_type or 'application/pdf'})
    except Exception:
        raise HTTPException(status_code=500, detail='Upload failed')
    file_url = f"https://{b}.s3.amazonaws.com/{key}"
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
    try:
        api_segment(paper_id, db)
    except Exception:
        p = db.query(PaperModel).filter(PaperModel.paper_id == paper_id).first()
        return {
            "status": "segment_error",
            "paper": {
                "paper_id": p.paper_id,
                "exam_id": p.exam_id,
                "test_code": p.test_code,
                "ta_id": p.ta_id,
                "file_name": p.file_name,
                "file_url": p.file_url,
                "submitted_at": p.submitted_at,
                "questions": p.questions,
            }
        }
    try:
        api_ocr(paper_id, db)
    except Exception:
        p = db.query(PaperModel).filter(PaperModel.paper_id == paper_id).first()
        return {
            "status": "ocr_error",
            "paper": {
                "paper_id": p.paper_id,
                "exam_id": p.exam_id,
                "test_code": p.test_code,
                "ta_id": p.ta_id,
                "file_name": p.file_name,
                "file_url": p.file_url,
                "submitted_at": p.submitted_at,
                "questions": p.questions,
            }
        }
    try:
        api_grade(paper_id, db)
    except Exception:
        p = db.query(PaperModel).filter(PaperModel.paper_id == paper_id).first()
        return {
            "status": "grade_error",
            "paper": {
                "paper_id": p.paper_id,
                "exam_id": p.exam_id,
                "test_code": p.test_code,
                "ta_id": p.ta_id,
                "file_name": p.file_name,
                "file_url": p.file_url,
                "submitted_at": p.submitted_at,
                "questions": p.questions,
            }
        }
    p = db.query(PaperModel).filter(PaperModel.paper_id == paper_id).first()
    return {
        "status": "ok",
        "paper": {
            "paper_id": p.paper_id,
            "exam_id": p.exam_id,
            "test_code": p.test_code,
            "ta_id": p.ta_id,
            "file_name": p.file_name,
            "file_url": p.file_url,
            "submitted_at": p.submitted_at,
            "questions": p.questions,
        }
    }

def upload_image_base64_to_mathpix(
    image_b64: str,
    retry_delay: int = 15,
    max_retries: int = 3,
    random_delay_range: tuple = (1, 15)
) -> Optional[Dict[str, Any]]:
    """
    将 Base64 编码的图像发送到 Mathpix API 进行 OCR。
    
    Args:
        image_b64: Base64 字符串（不含 data URI 前缀，如 'data:image/png;base64,'）
        retry_delay: 基础重试延迟（秒）
        max_retries: 最大重试次数
        random_delay_range: 随机抖动范围（秒）

    Returns:
        Mathpix 响应 JSON dict，或 None（失败）
    """
    retries = 0
    while retries < max_retries:
        try:
            # 构造 data URI 格式（Mathpix 要求）
            data_uri = f"data:image/png;base64,{image_b64}"

            r = requests.post(
                "https://api.mathpix.com/v3/text",
                data={
                    "src": data_uri,
                    "options_json": json.dumps({
                        "math_inline_delimiters": ["$", "$"],
                        "rm_spaces": True
                    })
                },
                headers=headers
            )

            if r.status_code == 200:
                response_data = r.json()
                print(f"[Mathpix] Success: {response_data.get('text', '')[:100]}...")
                return response_data

            elif r.status_code == 429:  # Rate limit
                random_delay = random.uniform(*random_delay_range)
                wait_time = retry_delay + random_delay
                print(f"[Mathpix] Rate limited. Retry {retries + 1}/{max_retries} in {wait_time:.2f}s")
                time.sleep(wait_time)
                retries += 1

            else:
                print(f"[Mathpix] Error {r.status_code}: {r.text}")
                return None

        except Exception as e:
            print(f"[Mathpix] Exception: {e}")
            return None

    print(f"[Mathpix] Max retries reached")
    return None

def image_to_base64(cv2_image: np.ndarray) -> str:
    """将 OpenCV 的 BGR 图像 (np.ndarray) 转为 Base64 编码的 PNG"""
    if cv2_image is None or cv2_image.size == 0:
        raise ValueError("Input image is empty or None")
    _, buffer = cv2.imencode('.png', cv2_image)
    return base64.b64encode(buffer).decode('utf-8')


def convert_pdf_to_images(pdf_path, dpi=300):
    """将PDF转换为OpenCV图像列表"""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
    try:
        images = convert_from_path(pdf_path, dpi=dpi)
    except Exception as e:
        raise Exception(f"PDF转换失败: {str(e)}")

    opencv_images = []
    for img in images:
        img_array = np.array(img)
        opencv_img = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        opencv_images.append(opencv_img)

    return opencv_images


def extract_questions(image):
    """从单页图像中提取问题区域"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    question_images = []

    contours = sorted(contours, key=lambda c: cv2.boundingRect(c)[1])
    print(f"共发现 {len(contours)} 个轮廓")
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        print(f"发现轮廓: x={x}, y={y}, w={w}, h={h}")
        ### 重要重要重要！！！ 调整阈值以适应不同尺寸的题目
        # if w > 100 and h > 120:
        if w > 100:
            question_img = image[y:y + h, x:x + w]
            question_images.append({
                'image': question_img,
                'bbox': (x, y, w, h)
            })

    return question_images


def process_single_pdf(pdf_path, s3_client, s3_bucket, exam_id, paper_id, region):
    """处理单个PDF文件并上传分割的图片到S3"""
    try:
        print(f"正在转换PDF: {pdf_path}")
        opencv_images = convert_pdf_to_images(pdf_path)
        
        total_questions = 0
        question_details = []
        
        for page_num, image in enumerate(opencv_images, 1):
            print(f"正在处理第 {page_num} 页")
            questions = extract_questions(image)
            
            for q_num, question_data in enumerate(questions, 1):
                total_questions += 1
                question_img = question_data['image']
                
                # 生成S3键名
                segment_key = f"segments/{exam_id}/{paper_id}/page{page_num}_q{total_questions}.png"
                
                # 将图片转换为字节
                success, encoded_image = cv2.imencode('.png', question_img)
                if not success:
                    print(f"无法编码第 {page_num} 页的第 {q_num} 个问题图片")
                    continue
                
                image_bytes = encoded_image.tobytes()
                
                # 上传到S3
                try:
                    s3_client.put_object(
                        Bucket=s3_bucket,
                        Key=segment_key,
                        Body=image_bytes,
                        ContentType='image/png'
                    )
                    segment_url = f"https://{s3_bucket}.s3.{region}.amazonaws.com/{segment_key}"
                    
                    question_details.append({
                        'question_id': total_questions,
                        'page_number': page_num,
                        's3_url': segment_url,
                        'bbox': question_data['bbox']  # 可选：保存边界框信息
                    })
                    
                    print(f"已上传分割图片 {total_questions} (第 {page_num} 页) 到 S3: {segment_url}")
                    
                except botocore.exceptions.ClientError as e:
                    print(f"上传分割图片到S3失败: {str(e)}")
                    continue

        print(f"处理完成! 共提取并上传 {total_questions} 张图片")
        return total_questions, question_details

    except Exception as e:
        print(f"处理PDF过程中发生错误: {str(e)}")
        raise
    

    # ocr
    
