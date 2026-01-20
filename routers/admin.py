from fastapi import APIRouter, Request, Form, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from urllib.parse import quote
from models.database import get_db
from models.user import User
from services.user_service import UserService
from services.exam_service import ExamService
from repositories.organization_repository import OrganizationRepository
from repositories.role_repository import RoleRepository
from routers.auth import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")

def require_admin(current_user: User | None) -> bool:
    """管理者権限をチェックして結果を返す"""
    return bool(current_user and current_user.is_admin)

def require_manager(current_user: User | None) -> bool:
    """管理権限をチェック（管理者または運用者）"""
    return bool(current_user and current_user.can_manage)

@router.get("/users", response_class=HTMLResponse)
async def admin_users_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """ユーザー一覧ページ"""
    if not require_manager(current_user):
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "管理権限が必要です"},
            status_code=403,
        )
    
    user_service = UserService(db)
    exam_service = ExamService(db)
    
    users = user_service.get_all_users()
    
    user_statuses = []
    for user in users:
        progress = exam_service.calculate_user_progress(user.id)
        user_statuses.append({
            'user': user,
            'status': progress['status'],
            'pass_count': progress['pass_count'],
            'total_exams': progress['total_exams']
        })
    
    return templates.TemplateResponse("admin_users.html", {
        "request": request,
        "current_user": current_user,
        "user_statuses": user_statuses
    })

@router.get("/history", response_class=HTMLResponse)
async def admin_history_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """受験履歴ページ"""
    if not require_manager(current_user):
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "管理権限が必要です"},
            status_code=403,
        )
    
    exam_service = ExamService(db)
    results = exam_service.get_all_results()
    
    return templates.TemplateResponse("admin_history.html", {
        "request": request,
        "results": results
    })

@router.get("/register", response_class=HTMLResponse)
async def register_page(
    request: Request,
    error: str | None = Query(None),
    success: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """ユーザー登録ページ"""
    if not require_manager(current_user):
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "管理権限が必要です"},
            status_code=403,
        )
    
    org_repository = OrganizationRepository(db)
    organizations = org_repository.get_all()
    
    return templates.TemplateResponse("admin_register.html", {
        "request": request,
        "current_user": current_user,
        "error": error,
        "success": success,
        "organizations": organizations
    })

@router.post("/register/confirm", response_class=HTMLResponse)
async def register_confirm(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    organization: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """ユーザー登録確認ページ"""
    if not require_manager(current_user):
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "管理権限が必要です"},
            status_code=403,
        )
    
    return templates.TemplateResponse("admin_register_confirm.html", {
        "request": request,
        "current_user": current_user,
        "email": email,
        "password": password,
        "confirm_password": confirm_password,
        "first_name": first_name,
        "last_name": last_name,
        "organization": organization
    })

@router.post("/register/execute")
async def register_execute(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    organization: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """ユーザー登録実行処理"""
    if not require_manager(current_user):
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "管理権限が必要です"},
            status_code=403,
        )
    
    user_service = UserService(db)
    
    error_msg = user_service.validate_registration(email, password, confirm_password, first_name, last_name, organization)
    if error_msg:
        # エラー時は確認ページをエラーメッセージ付きで再表示
        return templates.TemplateResponse("admin_register_confirm.html", {
            "request": request,
            "current_user": current_user,
            "email": email,
            "password": password,
            "confirm_password": confirm_password,
            "first_name": first_name,
            "last_name": last_name,
            "organization": organization,
            "error_message": error_msg
        })
    
    try:
        user_service.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            organization_name=organization
        )
        
        # 登録成功ページへ遷移
        return templates.TemplateResponse("admin_register_success.html", {
            "request": request,
            "current_user": current_user,
            "user_email": email,
            "user_first_name": first_name,
            "user_last_name": last_name,
            "user_organization": organization
        })

    except Exception as e:
        # 例外発生時も確認ページをエラーメッセージ付きで再表示
        return templates.TemplateResponse("admin_register_confirm.html", {
            "request": request,
            "current_user": current_user,
            "email": email,
            "password": password,
            "confirm_password": confirm_password,
            "first_name": first_name,
            "last_name": last_name,
            "organization": organization,
            "error_message": "ユーザー登録に失敗しました"
        })

@router.get("/users/{user_id}/chpasswd", response_class=HTMLResponse)
def change_password_page(
    user_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """パスワード変更ページ"""
    if not require_admin(current_user):
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "管理者のみアクセス可能"},
            status_code=403,
        )
    
    user_service = UserService(db)
    target_user = user_service.get_user_by_id(user_id)
    
    if not target_user:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "ユーザーが見つかりません"},
            status_code=404
        )
    
    return templates.TemplateResponse("admin_chpasswd.html", {
        "request": request,
        "current_user": current_user,
        "target_user": target_user
    })

@router.post("/users/{user_id}/chpasswd")
def change_password(
    user_id: int,
    request: Request,
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """パスワード変更処理"""
    if not require_admin(current_user):
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "管理者のみアクセス可能"},
            status_code=403,
        )
    
    if new_password != confirm_password:
        error_html = """
        <div class="bg-red-50 border-l-4 border-red-500 p-4 mb-6">
            <p class="text-red-700 font-semibold">エラー: パスワードが一致しません。</p>
        </div>
        """
        return HTMLResponse(content=error_html)
    
    user_service = UserService(db)
    target_user = user_service.update_password(user_id, new_password)
    
    if not target_user:
        error_html = """
        <div class="bg-red-50 border-l-4 border-red-500 p-4 mb-6">
            <p class="text-red-700 font-semibold">エラー: ユーザーが見つかりません。</p>
        </div>
        """
        return HTMLResponse(content=error_html)
    
    success_html = """
    <div class="bg-green-50 border-l-4 border-green-500 p-4 mb-6">
        <p class="text-green-700 font-semibold">パスワードを変更しました。</p>
    </div>
    """
    return HTMLResponse(content=success_html)

@router.get("/users/{user_id}/userdel", response_class=HTMLResponse)
def delete_user_page(
    user_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """ユーザー削除ページ"""
    if not require_admin(current_user):
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "管理者のみアクセス可能"},
            status_code=403,
        )
    
    user_service = UserService(db)
    target_user = user_service.get_user_by_id(user_id)
    
    if not target_user:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "ユーザーが見つかりません"},
            status_code=404
        )
    
    return templates.TemplateResponse("admin_userdel.html", {
        "request": request,
        "current_user": current_user,
        "target_user": target_user
    })

@router.post("/users/{user_id}/userdel")
def delete_user(
    user_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """ユーザー削除処理"""
    if not require_admin(current_user):
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "管理者のみアクセス可能"},
            status_code=403,
        )
    
    user_service = UserService(db)
    error_code = user_service.delete_user(user_id, current_user.id)
    
    if error_code:
        error_messages = {
            "cannot_delete_self": "自分自身を削除することはできません。",
            "user_not_found": "ユーザーが見つかりません。"
        }
        error_msg = error_messages.get(error_code, error_code)
        error_html = f"""
        <div class="bg-red-50 border-l-4 border-red-500 p-4 mb-6">
            <p class="text-red-700 font-semibold">エラー: {error_msg}</p>
        </div>
        """
        return HTMLResponse(content=error_html)
    
    return HTMLResponse(
        content='<div class="bg-green-50 border-l-4 border-green-500 p-4 mb-6"><p class="text-green-700 font-semibold">ユーザーを削除しました。</p></div>'
    )

@router.get("/users/{user_id}/roleedit")
def edit_role_page(
    user_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """ロール変更ページ"""
    if not require_admin(current_user):
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "管理者のみアクセス可能"},
            status_code=403,
        )
    
    user_service = UserService(db)
    role_repository = RoleRepository(db)
    
    target_user = user_service.get_user_by_id(user_id)
    
    if not target_user:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "ユーザーが見つかりません"},
            status_code=404
        )
    
    roles = role_repository.get_all()
    
    return templates.TemplateResponse("admin_roleedit.html", {
        "request": request,
        "current_user": current_user,
        "target_user": target_user,
        "roles": roles
    })

@router.post("/users/{user_id}/roleedit")
def edit_role(
    user_id: int,
    request: Request,
    role_id: int = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """ロール変更処理"""
    if not require_admin(current_user):
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "管理者のみアクセス可能"},
            status_code=403,
        )
    
    if user_id == current_user.id:
        error_html = """
        <div class="bg-red-50 border-l-4 border-red-500 p-4 mb-6">
            <p class="text-red-700 font-semibold">エラー: 自分自身のロールは変更できません。</p>
        </div>
        """
        return HTMLResponse(content=error_html)
    
    user_service = UserService(db)
    updated_user = user_service.update_user_role(user_id, role_id)
    
    if not updated_user:
        error_html = """
        <div class="bg-red-50 border-l-4 border-red-500 p-4 mb-6">
            <p class="text-red-700 font-semibold">エラー: ユーザーが見つかりません。</p>
        </div>
        """
        return HTMLResponse(content=error_html)

    success_html = """
    <div class="bg-green-50 border-l-4 border-green-500 p-4 mb-6">
        <p class="text-green-700 font-semibold">ロールを変更しました。</p>
    </div>
    """
    
    return HTMLResponse(content=success_html)