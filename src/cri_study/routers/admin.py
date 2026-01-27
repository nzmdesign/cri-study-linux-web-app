from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse

from models.user import User
from repositories.organization import OrganizationRepository, get_organization_repository
from repositories.role import RoleRepository, get_role_repository
from services.exam import ExamService, get_exam_service
from services.user import UserService, get_user_service
from utils.auth import require_admin, require_manager
from utils.template import templates


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_class=HTMLResponse)
async def admin_users_page(
    request: Request,
    current_user: User = Depends(require_manager),
    user_service: UserService = Depends(get_user_service),
    exam_service: ExamService = Depends(get_exam_service),
):
    """ユーザー一覧ページ"""
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
    current_user: User = Depends(require_manager),
    exam_service: ExamService = Depends(get_exam_service),
):
    """受験履歴ページ"""
    results = exam_service.get_all_results()
    
    return templates.TemplateResponse("admin_history.html", {
        "request": request,
        "results": results
    })


@router.get("/register", response_class=HTMLResponse)
async def register_page(
    request: Request,
    current_user: User = Depends(require_manager),
    org_repository: OrganizationRepository = Depends(get_organization_repository),
):
    """ユーザー登録ページ"""
    organizations = org_repository.get_all()
    
    return templates.TemplateResponse("admin_register.html", {
        "request": request,
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
    current_user: User = Depends(require_manager),
):
    """ユーザー登録確認ページ"""
    return templates.TemplateResponse(
        "admin_register_confirm.html",
        {
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
    current_user: User = Depends(require_manager),
    user_service: UserService = Depends(get_user_service),
):
    """ユーザー登録実行処理"""
    error_msg = user_service.validate_registration(
        email, password, confirm_password, first_name, last_name, organization
    )
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
    current_user: User = Depends(require_admin),
    user_service: UserService = Depends(get_user_service),
):
    """パスワード変更ページ"""
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
def change_password_confirm(
    user_id: int,
    request: Request,
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    current_user: User = Depends(require_admin),
    user_service: UserService = Depends(get_user_service),
):
    """パスワード変更確認画面"""
    # バリデーションチェック
    if new_password != confirm_password:
        error_html = """
        <div class="bg-red-50 border-l-4 border-red-500 p-4 mb-6">
            <p class="text-red-700 font-semibold">エラー: パスワードが一致しません。</p>
        </div>
        """
        return HTMLResponse(content=error_html)
    
    if len(new_password) < 4:
        error_html = """
        <div class="bg-red-50 border-l-4 border-red-500 p-4 mb-6">
            <p class="text-red-700 font-semibold">エラー: パスワードは4文字以上で入力してください。</p>
        </div>
        """
        return HTMLResponse(content=error_html)
    
    target_user = user_service.get_user_by_id(user_id)

    # 確認画面を表示
    response = templates.TemplateResponse("admin_chpasswd_confirm.html", {
        "request": request,
        "current_user": current_user,
        "target_user": target_user,
        "new_password": new_password,
        "confirm_password": confirm_password
    })
    response.headers["HX-Retarget"] = "body"
    response.headers["HX-Reswap"] = "innerHTML"
    return response


@router.post("/users/{user_id}/chpasswd/execute")
def change_password_execute(
    user_id: int,
    request: Request,
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    current_user: User = Depends(require_admin),
    user_service: UserService = Depends(get_user_service),
):
    """パスワード変更実行処理"""
    target_user = user_service.update_password(user_id, new_password)
    
    if not target_user:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "message": "ユーザーが見つかりません"},
            status_code=404
        )
    
    # 成功画面を表示
    return templates.TemplateResponse("admin_chpasswd_success.html", {
        "request": request,
        "current_user": current_user,
        "target_user": target_user
    })


@router.get("/users/{user_id}/userdel", response_class=HTMLResponse)
def delete_user_page(
    user_id: int,
    request: Request,
    current_user: User = Depends(require_admin),
    user_service: UserService = Depends(get_user_service),
):
    """ユーザー削除ページ"""
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
def delete_user_execute(
    user_id: int,
    request: Request,
    current_user: User = Depends(require_admin),
    user_service: UserService = Depends(get_user_service),
):
    """ユーザー削除実行処理"""
    target_user = user_service.get_user_by_id(user_id)
    
    if not target_user:
        error_html = """
        <div class="bg-red-50 border-l-4 border-red-500 p-4 mb-6">
            <p class="text-red-700 font-semibold">エラー: ユーザーが見つかりません。</p>
        </div>
        """
        return HTMLResponse(content=error_html)
    
    # 削除前にユーザー情報を保存
    deleted_user_email = target_user.email
    deleted_user_first_name = target_user.first_name
    deleted_user_last_name = target_user.last_name
    
    error_code = user_service.delete_user(user_id, current_user.id)

    if error_code == "cannot_delete_self":
        error_html = """
        <div class="bg-red-50 border-l-4 border-red-500 p-4 mb-6">
            <p class="text-red-700 font-semibold">エラー: 自分自身を削除することはできません。</p>
        </div>
        """
        return HTMLResponse(content=error_html)
        
    elif error_code == "cannot_delete_admin":
        error_html = """
        <div class="bg-red-50 border-l-4 border-red-500 p-4 mb-6">
            <p class="text-red-700 font-semibold">エラー: 管理者ユーザーは削除できません。</p>
        </div>
        """
        return HTMLResponse(content=error_html)
    
    elif error_code == "user_not_found":
        error_html = """
        <div class="bg-red-50 border-l-4 border-red-500 p-4 mb-6">
            <p class="text-red-700 font-semibold">エラー: ユーザーが見つかりません。</p>
        </div>
        """
        return HTMLResponse(content=error_html)
    
    # 成功画面を表示
    response = templates.TemplateResponse("admin_userdel_success.html", {
        "request": request,
        "current_user": current_user,
        "deleted_user_email": deleted_user_email,
        "deleted_user_first_name": deleted_user_first_name,
        "deleted_user_last_name": deleted_user_last_name
    })    
    response.headers["HX-Retarget"] = "body"
    response.headers["HX-Reswap"] = "innerHTML"
    return response


@router.get("/users/{user_id}/roleedit")
def edit_role_page(
    user_id: int,
    request: Request,
    current_user: User = Depends(require_admin),
    user_service: UserService = Depends(get_user_service),
    role_repository: RoleRepository = Depends(get_role_repository),
):
    """ロール変更ページ"""
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
def edit_role_confirm(
    user_id: int,
    request: Request,
    role_id: int = Form(...),
    current_user: User = Depends(require_admin),
    user_service: UserService = Depends(get_user_service),
    role_repository: RoleRepository = Depends(get_role_repository),
):
    """ロール変更確認画面"""
    # 自分自身のロール変更チェック
    if user_id == current_user.id:
        error_html = """
        <div class="bg-red-50 border-l-4 border-red-500 p-4 mb-6">
            <p class="text-red-700 font-semibold">エラー: 自分自身のロールは変更できません。</p>
        </div>
        """
        return HTMLResponse(content=error_html)
    
    target_user = user_service.get_user_by_id(user_id)
    
    # 新しいロールを取得
    new_role = role_repository.get_by_id(role_id)
    
    # 確認画面を表示
    response = templates.TemplateResponse("admin_roleedit_confirm.html", {
        "request": request,
        "current_user": current_user,
        "target_user": target_user,
        "current_role_name": target_user.role.name,
        "new_role_id": role_id,
        "new_role_name": new_role.name
    })
    response.headers["HX-Retarget"] = "body"
    response.headers["HX-Reswap"] = "innerHTML"
    return response


@router.post("/users/{user_id}/roleedit/execute")
def edit_role_execute(
    user_id: int,
    request: Request,
    role_id: int = Form(...),
    current_user: User = Depends(require_admin),
    user_service: UserService = Depends(get_user_service),
):
    """ロール変更実行処理"""
    updated_user = user_service.update_user_role(user_id, role_id)
    
    if not updated_user:
        error_html = """
        <div class="bg-red-50 border-l-4 border-red-500 p-4 mb-6">
            <p class="text-red-700 font-semibold">エラー: ロールの変更に失敗しました。</p>
        </div>
        """
        return HTMLResponse(content=error_html)
    
    # 成功画面を表示
    response = templates.TemplateResponse("admin_roleedit_success.html", {
        "request": request,
        "current_user": current_user,
        "target_user": updated_user
    })    
    response.headers["HX-Retarget"] = "body"
    response.headers["HX-Reswap"] = "innerHTML"
    return response

