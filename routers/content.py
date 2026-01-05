from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from models.database import get_db
from models.user import User
from services.content_service import ContentService
from routers.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """トップページ"""
    if not current_user:
        return RedirectResponse(url='/login', status_code=302)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "current_user": current_user
    })

@router.get("/text/{text_id}", response_class=HTMLResponse)
async def text_page(
    request: Request,
    text_id: int,
    current_user: User = Depends(get_current_user)
):
    """テキストページ"""
    if not current_user:
        return RedirectResponse(url='/login', status_code=302)
    
    content_service = ContentService()
    html_content, title = content_service.get_text_content(text_id)
    
    if not html_content:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "message": "ページが見つかりません"
        }, status_code=404)
    
    return templates.TemplateResponse("content.html", {
        "request": request,
        "content": html_content,
        "title": title
    })

@router.get("/setup/{setup_type}", response_class=HTMLResponse)
async def setup_page(
    request: Request,
    setup_type: str,
    current_user: User = Depends(get_current_user)
):
    """環境構築ページ"""
    if not current_user:
        return RedirectResponse(url='/login', status_code=302)
    
    content_service = ContentService()
    html_content, title = content_service.get_setup_content(setup_type)
    
    if not html_content:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "message": "ページが見つかりません"
        }, status_code=404)
    
    return templates.TemplateResponse("content.html", {
        "request": request,
        "content": html_content,
        "title": title
    })

@router.get("/guide", response_class=HTMLResponse)
async def guide_page(request: Request):
    """受講案内ページ"""
    content_service = ContentService()
    html_content, title = content_service.get_guide_content()
    
    if not html_content:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "message": "ページが見つかりません"
        }, status_code=404)
    
    return templates.TemplateResponse("content.html", {
        "request": request,
        "content": html_content,
        "title": title
    })

@router.get("/manual", response_class=HTMLResponse)
async def manual_page(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """運用マニュアルページ"""
    if not current_user:
        return RedirectResponse(url='/login', status_code=302)
    
    if not current_user.can_manage:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "message": "アクセス不可"
        }, status_code=403)
    
    content_service = ContentService()
    html_content, title = content_service.get_manual_content()
    
    if not html_content:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "message": "ページが見つかりません"
        }, status_code=404)
    
    return templates.TemplateResponse("content.html", {
        "request": request,
        "content": html_content,
        "title": title
    })
