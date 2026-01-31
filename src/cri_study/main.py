from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from init_database import initialize_database
from routers import admin_router, auth_router, exam_router, health_router, index_router
from utils.auth import ForbiddenException, UnauthenticatedException
from utils.template import templates


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    # スタートアップ
    print("アプリケーション起動中...")
    initialize_database()
    print("データベース初期化完了")
    yield
    # シャットダウン
    print("アプリケーション終了")


app = FastAPI(lifespan=lifespan)

# 例外ハンドラー
@app.exception_handler(UnauthenticatedException)
async def unauthenticated_exception_handler(request: Request, exc: UnauthenticatedException):
    """未認証例外ハンドラー - ログインページにリダイレクト"""
    return RedirectResponse(url="/login", status_code=303)


@app.exception_handler(ForbiddenException)
async def forbidden_exception_handler(request: Request, exc: ForbiddenException):
    """権限不足例外ハンドラー - エラーページを表示"""
    return templates.TemplateResponse(
        "error.html",
        {"request": request, "error_message": "このページにアクセスする権限がありません。"},
        status_code=403,
    )

# 静的ファイルの設定
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# ルーターの登録
app.include_router(health_router)
app.include_router(index_router)
app.include_router(auth_router)
app.include_router(exam_router)
app.include_router(admin_router)
