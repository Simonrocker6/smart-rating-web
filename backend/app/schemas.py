from pydantic import BaseModel, field_serializer
from uuid import UUID
from datetime import datetime
from typing import List, Any, Optional

class Rubric(BaseModel):
    rubric_title: str
    rubric_template: str

class Question(BaseModel):
    question_id: int
    max_score: float
    correct_answer: str
    solution_page: int
    final_answer_page: int
    rubrics: List[Rubric]

class Exam(BaseModel):
    exam_id: UUID
    title: str
    total_questions: int
    created_at: datetime
    questions: List[Any]
    total_images: Optional[int] = None

class ExamCreate(BaseModel):
    title: str
    total_questions: int
    created_at: str
    questions: List[Question]
    total_images: Optional[int] = None

class ExamUpdate(BaseModel):
    title: Optional[str] = None
    total_questions: Optional[int] = None
    created_at: Optional[str] = None
    questions: Optional[List[Question]] = None
    total_images: Optional[int] = None

class TA(BaseModel):
    ta_id: int
    ta_name: str
    email: str

class TACreate(BaseModel):
    ta_name: str
    email: str

class TAUpdate(BaseModel):
    ta_name: Optional[str] = None
    email: Optional[str] = None

class PaperQuestion(BaseModel):
    question_id: int
    solution_image_url: str
    final_answer_image_url: str
    ai_grading: dict

class Paper(BaseModel):
    paper_id: str
    exam_id: str
    test_code: str
    ta_id: int
    file_name: str
    file_url: str
    submitted_at: str
    questions: List[PaperQuestion]

class PaperCreate(BaseModel):
    exam_id: str
    test_code: str
    ta_id: int
    file_name: str
    file_url: str
    questions: List[PaperQuestion]
