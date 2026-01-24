from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from models.user import User
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
