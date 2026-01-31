from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from models.user import User
from utils.auth import require_authenticated
from utils.template import templates


router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, current_user: User = Depends(require_authenticated)):
    """トップページ"""

    return templates.TemplateResponse(
        "index.html", {"request": request, "current_user": current_user}
    )
