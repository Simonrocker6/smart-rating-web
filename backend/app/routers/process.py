from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from ..db import SessionLocal, init_db, ExamModel, PaperModel
from sqlalchemy import select
from ..s3 import key_to_url
from urllib.parse import urlparse
import fitz
import boto3
import cv2
import numpy as np
import os
import time
import uuid
import json
import requests

router = APIRouter()

def get_db():
    init_db()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _get_exam(db: Session, exam_id: str) -> Optional[ExamModel]:
    return db.query(ExamModel).filter(ExamModel.exam_id == exam_id).first()

def _get_paper(db: Session, paper_id: str) -> Optional[PaperModel]:
    return db.query(PaperModel).filter(PaperModel.paper_id == paper_id).first()

@router.post('/segment')
def api_segment(paper_id: str, db: Session = Depends(get_db)):
    p = _get_paper(db, paper_id)
    if not p:
        raise HTTPException(status_code=404, detail='paper not found')
    exam = _get_exam(db, p.exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail='exam not found')
    questions = (exam.rubrics or {}).get('questions', [])
    total = len(questions)
    expected = exam.total_images if getattr(exam, 'total_images', None) else (total * 2 + 1)
    bucket = os.getenv('S3_BUCKET_UPLOADS_PROD') or os.getenv('S3_BUCKET_UPLOADS') or os.getenv('S3_BUCKET')
    if not bucket:
        raise HTTPException(status_code=400, detail='S3 bucket not configured')
    # write segmented images under segments/<exam_id>/<paper_id>/<uuid>/
    base = f"segments/{p.exam_id}/{p.paper_id}/{uuid.uuid4().hex}"
    # download original PDF from S3
    parsed = urlparse(p.file_url)
    path = parsed.path.lstrip('/')
    if '.s3' in parsed.netloc:
        src_bucket = parsed.netloc.split('.s3')[0]
        src_key = path
    else:
        # fallback to configured bucket
        src_bucket = bucket
        src_key = path
    s3 = boto3.client('s3', region_name=os.getenv('AWS_REGION'))
    try:
        obj = s3.get_object(Bucket=src_bucket, Key=src_key)
        pdf_bytes = obj['Body'].read()
    except Exception:
        raise HTTPException(status_code=500, detail='PDF fetch failed')
    # render pages and perform contour-based segmentation
    try:
        doc = fitz.open(stream=pdf_bytes, filetype='pdf')
    except Exception:
        raise HTTPException(status_code=500, detail='PDF convert failed')
    figure_keys: list[str] = []
    # first figure: test_code from the first page
    try:
        page0 = doc.load_page(0)
        pix0 = page0.get_pixmap()
        img0 = np.frombuffer(pix0.samples, dtype=np.uint8).reshape(pix0.height, pix0.width, pix0.n)
        if pix0.n == 4:
            img0 = cv2.cvtColor(img0, cv2.COLOR_RGBA2BGR)
        else:
            img0 = cv2.cvtColor(img0, cv2.COLOR_RGB2BGR)
        test_code_key = f"{base}/figure1_test_code.png"
        _, buf = cv2.imencode('.png', img0)
        s3.put_object(Bucket=bucket, Key=test_code_key, Body=buf.tobytes(), ContentType='image/png')
        figure_keys.append(test_code_key)
    except Exception:
        raise HTTPException(status_code=500, detail='Test code render failed')
    # subsequent figures: detect question blocks across all pages
    def extract_blocks(bgr_img):
        gray = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY_INV,11,2)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=lambda c: cv2.boundingRect(c)[1])
        blocks = []
        for cnt in contours:
            x,y,w,h = cv2.boundingRect(cnt)
            if w > 100 and h > 120:
                blocks.append((x,y,w,h))
        return blocks
    try:
        for page_num in range(doc.page_count):
            pg = doc.load_page(page_num)
            pix = pg.get_pixmap()
            arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
            if pix.n == 4:
                bgr = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
            else:
                bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
            blocks = extract_blocks(bgr)
            for (x,y,w,h) in blocks:
                crop = bgr[y:y+h, x:x+w]
                _, buf = cv2.imencode('.png', crop)
                fig_key = f"{base}/figure{len(figure_keys)+1}.png"
                s3.put_object(Bucket=bucket, Key=fig_key, Body=buf.tobytes(), ContentType='image/png')
                figure_keys.append(fig_key)
    except Exception:
        raise HTTPException(status_code=500, detail='Contour segmentation failed')
    # validate count
    if len(figure_keys) != expected:
        p.questions = []
        db.commit()
        return {"error_code": "SEGMENT_ERROR"}
    # map figures to questions sequentially: figure1=test_code, then pairs per question
    qlist = []
    for idx, q in enumerate(questions):
        # figures: [figure1_test_code, figure2, figure3, figure4, ...]
        sol_key = figure_keys[1 + idx*2]
        fin_key = figure_keys[1 + idx*2 + 1]
        qlist.append({
            "question_id": q["question_id"],
            "solution_image_url": key_to_url(bucket, sol_key),
            "final_answer_image_url": key_to_url(bucket, fin_key),
            "ai_grading": { "score": 0.0, "explanation": "", "graded_at": None }
        })
    p.questions = qlist
    db.commit()
    return {"ok": True, "images": qlist}

@router.post('/ocr')
def api_ocr(paper_id: str, db: Session = Depends(get_db)):
    p = _get_paper(db, paper_id)
    if not p:
        raise HTTPException(status_code=404, detail='paper not found')
    app_id = os.getenv('MATHPIX_APP_ID')
    app_key = os.getenv('MATHPIX_APP_KEY')
    use_mathpix = bool(app_id and app_key)
    # OCR test code from figure1
    test_code = None
    try:
        # reconstruct figure1 key from an image URL in questions, or derive base path
        # The first figure is stored as .../figure1_test_code.png
        img_url_any = p.questions[0]['solution_image_url'] if p.questions else None
        bucket_guess = None
        base_prefix = None
        if img_url_any:
            parsed = urlparse(img_url_any)
            bucket_guess = parsed.netloc.split('.s3')[0]
            key_any = parsed.path.lstrip('/')
            # remove trailing file name and stay in the same directory
            if '/' in key_any:
                base_prefix = key_any.rsplit('/', 1)[0]
        if bucket_guess and base_prefix:
            figure1_key = f"{base_prefix}/figure1_test_code.png"
            s3 = boto3.client('s3', region_name=os.getenv('AWS_REGION'))
            presigned = s3.generate_presigned_url('get_object', Params={'Bucket': bucket_guess, 'Key': figure1_key}, ExpiresIn=600)
            headers_tc = {"app_id": app_id, "app_key": app_key}
            r_tc = requests.post('https://api.mathpix.com/v3/text', headers=headers_tc, json={"src": presigned, "formats": ["text"]}, timeout=30)
            if r_tc.status_code == 200:
                data_tc = r_tc.json()
                text_tc = data_tc.get('text') or ''
                test_code = (text_tc or '').replace('$','').strip()
    except Exception:
        test_code = None
    if test_code:
        p.test_code = test_code
    # OCR per question images
    for q in p.questions:
        if use_mathpix:
            headers = {"app_id": app_id, "app_key": app_key}
            def call(img_url):
                try:
                    parsed = urlparse(img_url)
                    bucket = parsed.netloc.split('.s3')[0]
                    key = parsed.path.lstrip('/')
                    s3 = boto3.client('s3', region_name=os.getenv('AWS_REGION'))
                    presigned = s3.generate_presigned_url('get_object', Params={'Bucket': bucket, 'Key': key}, ExpiresIn=600)
                    r = requests.post('https://api.mathpix.com/v3/text', headers=headers, json={"src": presigned, "formats": ["latex_simplified"]}, timeout=30)
                    if r.status_code == 200:
                        data = r.json()
                        return data.get('latex_simplified') or ''
                except Exception:
                    return ''
                return ''
            sol = call(q.get('solution_image_url', ''))
            fin = call(q.get('final_answer_image_url', ''))
            q['solution_latex'] = sol
            q['final_answer_latex'] = fin
        else:
            # fallback stub
            q['solution_latex'] = ''
            q['final_answer_latex'] = ''
    db.commit()
    return {"ok": True, "test_code": test_code}

@router.post('/grade')
def api_grade(paper_id: str, db: Session = Depends(get_db)):
    p = _get_paper(db, paper_id)
    if not p:
        raise HTTPException(status_code=404, detail='paper not found')
    exam = _get_exam(db, p.exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail='exam not found')
    questions = (exam.rubrics or {}).get('questions', [])
    # call OpenAI if key available
    api_key = os.getenv('OPENAI_API_KEY')
    for q in p.questions:
        max_score = float(next((qq.get('max_score') for qq in questions if qq.get('question_id') == q.get('question_id')), 0.0))
        prompt = {
            "solution": q.get('solution_latex', ''),
            "final_answer": q.get('final_answer_latex', ''),
            "correct_answer": next((qq.get('correct_answer') for qq in questions if qq.get('question_id') == q.get('question_id')), ''),
            "rubrics": next((qq.get('rubrics') for qq in questions if qq.get('question_id') == q.get('question_id')), []),
            "max_score": max_score
        }
        explanation = ""
        score = 0.0
        if api_key:
            try:
                headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                payload = {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": "Return JSON with fields score (0..max_score) and explanation."},
                        {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)}
                    ]
                }
                r = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=payload, timeout=60)
                if r.status_code == 200:
                    data = r.json()
                    txt = data['choices'][0]['message']['content']
                    try:
                        j = json.loads(txt)
                        score = float(j.get('score', 0.0))
                        explanation = str(j.get('explanation', ''))[:2000]
                    except Exception:
                        explanation = txt[:2000]
            except Exception:
                pass
        q['ai_grading'] = {"score": score, "explanation": explanation, "graded_at": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    db.commit()
    return {"ok": True, "paper_id": paper_id}
