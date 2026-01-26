import logging
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from database import initialize_database
from routers import auth_router, exam_router, admin_router, health_router, index_router

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# 静的ファイルの設定
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# ルーターの登録
app.include_router(health_router)
app.include_router(index_router)
app.include_router(auth_router)
app.include_router(exam_router)
app.include_router(admin_router)

# データベースの初期化
@app.on_event("startup")
def startup_event():
    initialize_database()
