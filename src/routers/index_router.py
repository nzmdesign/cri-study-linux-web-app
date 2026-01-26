from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from models.user import User
from src.routers.auth_router import get_current_user
import os

router = APIRouter()
templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
templates = Jinja2Templates(directory=templates_dir)

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
