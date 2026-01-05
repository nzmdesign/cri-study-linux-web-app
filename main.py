import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from models.database import create_tables
from database import initialize_database
from routers import auth_router, content_router, exam_router, admin_router

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# 静的ファイルの設定
app.mount("/static", StaticFiles(directory="static"), name="static")

# ルーターの登録
app.include_router(auth_router)
app.include_router(content_router)
app.include_router(exam_router)
app.include_router(admin_router)

# データベースの初期化
@app.on_event("startup")
def startup_event():
    initialize_database()
