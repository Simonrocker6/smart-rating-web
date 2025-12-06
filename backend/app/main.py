from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers.exams import router as exams_router
from .routers.tas import router as tas_router
from .routers.files import router as files_router
from .routers.papers import router as papers_router
from .routers.health import router as health_router
from .routers.process import router as process_router
from .routers.upload import router as upload_router
from .routers.pipeline import router as pipeline_router
import os
try:
    from dotenv import load_dotenv
    # Load backend/.env if present
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
except Exception:
    pass
from .db import init_db  # ← 导入 init_db
from contextlib import asynccontextmanager
from dotenv import load_dotenv  # ← 新增导入
from os import getenv


load_dotenv()
print(f"#### ENV: {getenv('ENV', )}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()  # 只在服务启动时运行一次
    yield
    # Shutdown (可选)
    pass

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(exams_router, prefix="/exams", tags=["exams"])
app.include_router(tas_router, prefix="/tas", tags=["tas"])
app.include_router(files_router, prefix="/files", tags=["files"])
app.include_router(papers_router, prefix="/papers", tags=["papers"])
app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(process_router, prefix="/process", tags=["process"])
app.include_router(upload_router, prefix="/upload", tags=["upload"])
app.include_router(pipeline_router, prefix="/pipeline", tags=["pipeline"])
