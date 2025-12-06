from sqlalchemy import create_engine, Column, String, Integer, DateTime, UniqueConstraint
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.types import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from .config import get_database_url

DATABASE_URL = get_database_url()
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

JSONType = JSONB if DATABASE_URL.startswith("postgresql") else JSON

class ExamModel(Base):
    __tablename__ = "exams"
    exam_id = Column(PG_UUID(as_uuid=True), primary_key=True, index=True)  
    title = Column(String, nullable=False)
    total_questions = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)          
    rubrics = Column(JSONType, nullable=False)
    total_images = Column(Integer, nullable=True)

class TAModel(Base):
    __tablename__ = "tas"
    ta_id = Column(Integer, primary_key=True, index=True)
    ta_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    __table_args__ = (UniqueConstraint('email', name='uq_ta_email'),)

class PaperModel(Base):
    __tablename__ = "papers"
    paper_id = Column(String, primary_key=True, index=True)
    exam_id = Column(String, nullable=False)
    test_code = Column(String, nullable=False)
    ta_id = Column(Integer, nullable=False)
    file_name = Column(String, nullable=False)
    file_url = Column(String, nullable=True)
    submitted_at = Column(String, nullable=False)
    questions = Column(JSONType, nullable=False)

def init_db():
    Base.metadata.create_all(bind=engine)
    _ensure_exams_data_column()
    _ensure_papers_file_url_column()
    _ensure_exams_total_images_column()

def _ensure_exams_data_column():
    try:
        if engine.url.drivername.startswith("postgresql"):
            with engine.connect() as conn:
                conn.exec_driver_sql(
                    """
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name='exams' AND column_name='data'
                        ) THEN
                            ALTER TABLE exams ADD COLUMN data JSONB NOT NULL DEFAULT '{}'::jsonb;
                        END IF;
                    END $$;
                    """
                )
    except Exception:
        pass

def _ensure_papers_file_url_column():
    try:
        if engine.url.drivername.startswith("postgresql"):
            with engine.connect() as conn:
                conn.exec_driver_sql(
                    """
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name='papers' AND column_name='file_url'
                        ) THEN
                            ALTER TABLE papers ADD COLUMN file_url text;
                        END IF;
                    END $$;
                    """
                )
    except Exception:
        pass

def _ensure_exams_total_images_column():
    try:
        if engine.url.drivername.startswith("postgresql"):
            with engine.connect() as conn:
                conn.exec_driver_sql(
                    """
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name='exams' AND column_name='total_images'
                        ) THEN
                            ALTER TABLE exams ADD COLUMN total_images integer;
                            UPDATE exams SET total_images = 2 * jsonb_array_length(rubrics->'questions') + 1;
                        END IF;
                    END $$;
                    """
                )
    except Exception:
        pass
