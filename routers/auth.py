from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from models.database import get_db
from models.user import User
from services.auth_service import AuthService

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    """Cookieから現在のユーザーを取得"""
    email = request.cookies.get("user")
    login_hash = request.cookies.get("login_hash")
    
    auth_service = AuthService(db)
    return auth_service.get_current_user(email, login_hash)

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """ログインページ"""
    error = request.query_params.get("error")
    error_message = None

    if error:
        error_message = error
    
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": error_message
    })

@router.post("/login")
async def login(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """ログイン処理"""
    auth_service = AuthService(db)
    user = auth_service.authenticate(email, password)
    
    if not user:
        return RedirectResponse(url="/login?error=invalid_credentials", status_code=302)
    
    # 認証成功
    login_hash = auth_service.generate_login_hash(user)
    response = RedirectResponse(url='/', status_code=302)
    response.set_cookie(key="user", value=email, httponly=True, secure=False, samesite="strict")
    response.set_cookie(key="login_hash", value=login_hash, httponly=True, secure=False, samesite="strict")
    return response

@router.get("/logout")
async def logout():
    """ログアウト処理"""
    response = RedirectResponse(url='/', status_code=302)
    response.delete_cookie("user")
    response.delete_cookie("login_hash")
    return response
