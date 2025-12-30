import json
import os
import glob
from pathlib import Path
import bcrypt
import logging
import hashlib
from datetime import datetime
from urllib.parse import quote
from database import get_db, initialize_database, User, ExamResult, Organization, get_all_organizations
from fastapi import FastAPI, Request, HTTPException, Form, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

class Answer(BaseModel):
    question_id: int
    selected_option: int

class SubmitExamRequest(BaseModel):
    answers: list[Answer]

app = FastAPI()

# 静的ファイルとテンプレートの設定
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# JSONファイルから試験データを読み込み
def load_exam_data():
    """
    content/exam/ ディレクトリから各試験ファイル {exam_id}.json を読み込む
    """
    exam_dir = Path("content/exam")
    exams = {}

    if not exam_dir.exists() or not exam_dir.is_dir():
        print("警告: content/exam ディレクトリが見つかりません")
        return exams

    # 各 {exam_id}.json ファイルを読み込む
    for exam_file in sorted(exam_dir.glob("*.json")):
        try:
            # ファイル名から exam_id を抽出
            exam_id = int(exam_file.stem)
        except Exception:
            # 数字ファイル名でない場合はスキップ
            continue

        try:
            with open(exam_file, "r", encoding="utf-8") as f:
                exam_data = json.load(f)
                exams[exam_id] = exam_data
        except Exception:
            print(f"警告: {exam_file} の読み込みに失敗しました")
            continue

    return exams

exam_data = load_exam_data()

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# データベースの初期化
@app.on_event("startup")
def startup_event():
    initialize_database()

# Cookieから現在のユーザーを取得
def get_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    email = request.cookies.get("user")
    if not email:
        return None
    
    # ユーザー情報を取得
    user = db.query(User).filter(User.email == email, User.deleted_at.is_(None)).first()
    if not user:
        return None
    
    # 追加のセキュリティチェック（Cookie改ざん防止）
    login_hash = request.cookies.get("login_hash")
    if not login_hash:
        return None
    
    # ユーザー固有の情報からハッシュを生成して検証
    expected_hash = hashlib.sha256(f"{user.id}{user.email}{user.hashed_password}".encode()).hexdigest()
    
    if login_hash != expected_hash:
        return None
    
    return user

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def redirect_with_message(message: str, is_error: bool = True):
    """メッセージ付きでリダイレクト"""
    param = "register_error" if is_error else "register_success"
    return RedirectResponse(url=f'/admin/register?{param}={quote(message)}', status_code=302)

def validate_registration(email: str, password: str, confirm_password: str, first_name: str, last_name: str, db: Session):
    """ユーザー登録のバリデーション"""
    if password != confirm_password:
        return "パスワードが一致しません"
    if len(password) < 4:
        return "パスワードは4文字以上にしてください"
    if not email or "@" not in email:
        return "有効なメールアドレスを入力してください"
    if not first_name or not last_name:
        return "姓名を入力してください"
    if db.query(User).filter(User.email == email, User.deleted_at.is_(None)).first():
        return "このメールアドレスは既に使用されています"
    return None

def require_admin(current_user: Optional[User]):
    """管理者権限をチェックする"""
    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="管理者のみアクセス可能")
    return current_user

# トップページ
@app.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    current_user: User = Depends(get_current_user)
    ):
    if not current_user:
        return RedirectResponse(url='/login', status_code=302)
    return templates.TemplateResponse("index.html", {"request": request, "current_user": current_user})

# ログインページ
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# ログイン処理
@app.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email, User.deleted_at.is_(None)).first()

    # ユーザーが存在しない、削除されている、またはパスワードが一致しない場合
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {"request": request, "error": "メールアドレスまたはパスワードが正しくありません"})

    # 認証成功 - セキュリティハッシュも設定
    login_hash = hashlib.sha256(f"{user.id}{user.email}{user.hashed_password}".encode()).hexdigest()
    response = RedirectResponse(url='/', status_code=302)
    response.set_cookie(key="user", value=email, httponly=True, secure=False, samesite="strict")
    response.set_cookie(key="login_hash", value=login_hash, httponly=True, secure=False, samesite="strict")
    return response

# ログアウト処理
@app.get("/logout")
async def logout():
    response = RedirectResponse(url='/', status_code=302)
    response.delete_cookie("user")
    response.delete_cookie("login_hash")
    return response

# 受講案内ページ
@app.get("/guide", response_class=HTMLResponse)
async def guide_page(request: Request):

    file_path = f"content/guide/guide.html"

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="ページが見つかりません")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        # タイトルを設定
        title = f"受講案内"

        return templates.TemplateResponse("content.html", {
            "request": request,
            "content": html_content,
            "title": title
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail="ファイルの読み込みエラー")

# テキストページ
@app.get("/text/{text_id}", response_class=HTMLResponse)
async def text_page(
    request: Request,
    text_id: int,
    current_user: User = Depends(get_current_user)
    ):
    if not current_user:
        return RedirectResponse(url='/login', status_code=302)

    file_path = f"content/text/{text_id}.html"

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="テキストが見つかりません")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        # タイトルを設定
        title = f"第{text_id}回テキスト"

        return templates.TemplateResponse("content.html", {
            "request": request,
            "content": html_content,
            "title": title
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail="ファイルの読み込みエラー")

# 演習ページ
@app.get("/practice/{practice_id}", response_class=HTMLResponse)
async def practice_page(
    request: Request,
    practice_id: int,
    current_user: User = Depends(get_current_user)
    ):
    if not current_user:
        return RedirectResponse(url='/login', status_code=302)

    file_path = f"content/practice/{practice_id}.html"

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="テキストが見つかりません")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        # タイトルを設定
        title = f"第{practice_id}回演習"

        return templates.TemplateResponse("content.html", {
            "request": request,
            "content": html_content,
            "title": title
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail="ファイルの読み込みエラー")

# 環境構築ページ
@app.get("/setup/{setup_type}", response_class=HTMLResponse)
async def setup_page(
    request: Request,
    setup_type: str,
    current_user: User = Depends(get_current_user)
    ):
    if not current_user:
        return RedirectResponse(url='/login', status_code=302)

    if setup_type not in ["windows", "mac"]:
        raise HTTPException(status_code=404, detail="ページが見つかりません")

    file_path = f"content/setup/{setup_type}.html"

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="ガイドが見つかりません")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        # タイトルを設定
        title = f"{setup_type.capitalize()}向け環境構築ガイド"

        return templates.TemplateResponse("content.html", {
            "request": request,
            "content": html_content,
            "title": title
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail="ファイルの読み込みエラー")

@app.get("/exam/{exam_id}", response_class=HTMLResponse)
async def exam_page(
    request: Request,
    exam_id: int,
    current_user: User = Depends(get_current_user)
    ):
    if not current_user:
        return RedirectResponse(url='/login', status_code=302)

    if exam_id not in exam_data:
        return templates.TemplateResponse("error.html", {"request": request, "message": "試験が見つかりません"})

    exam = exam_data[exam_id]
    return templates.TemplateResponse("exam.html", {"request": request, "exam": exam, "exam_id": exam_id})

@app.post("/api/exam/{exam_id}/submit")
async def submit_exam(
    request: Request,
    exam_id: int,
    submit_data: SubmitExamRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
    ):

    if not current_user:
        raise HTTPException(status_code=401, detail="認証が必要です")

    if exam_id not in exam_data:
        raise HTTPException(status_code=400, detail="試験が見つかりません")

    exam = exam_data[exam_id]
    questions = exam["questions"]
    answers = [{"question_id": a.question_id, "selected_option": a.selected_option} for a in submit_data.answers]

    # 採点処理
    correct_count = 0

    for question in questions:
        # ユーザーの回答を探す
        for answer in answers:
            if answer["question_id"] == question["id"]:
                if answer["selected_option"] == question["correct"]:
                    correct_count += 1
                break

    # データベースに結果を保存
    exam_result = ExamResult(
        user_id=current_user.id,
        exam_id=exam_id,
        exam_title=exam["title"],
        correct_count=correct_count,
        total_questions=len(questions),
        score_percentage=round((correct_count / len(questions)) * 100, 1),
        details=None  # 詳細結果は保存しない
    )
    db.add(exam_result)
    db.commit()

    # 結果ページにリダイレクトするために、結果IDを返す
    return {"result_id": exam_result.id, "redirect_url": f"/exam/{exam_id}/result/{exam_result.id}"}

@app.get("/exam/{exam_id}/result/{result_id}", response_class=HTMLResponse)
async def exam_result_page(
    request: Request,
    exam_id: int,
    result_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
    ):

    if not current_user:
        return RedirectResponse(url='/login', status_code=302)

    # 結果を取得
    exam_result = db.query(ExamResult).filter(
        ExamResult.id == result_id,
        ExamResult.user_id == current_user.id,
        ExamResult.exam_id == exam_id
    ).first()

    if not exam_result:
        return templates.TemplateResponse("error.html", {
            "request": request, 
            "message": "結果が見つかりません"
        })

    is_passed = exam_result.correct_count == exam_result.total_questions

    return templates.TemplateResponse("exam_result.html", {
        "request": request,
        "exam_id": exam_id,
        "exam_title": exam_result.exam_title,
        "correct_count": exam_result.correct_count,
        "total_questions": exam_result.total_questions,
        "is_passed": is_passed
    })

@app.get("/mypage", response_class=HTMLResponse)
async def mypage(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
    ):
    if not current_user:
        return RedirectResponse(url='/login', status_code=302)

    # 試験データから全ての試験情報を取得
    exam_statuses = []

    # 各試験IDに対して受験状況を確認
    for exam_id in exam_data.keys():
        exam_title = exam_data[exam_id]["title"]

        # 最新の受験結果を取得（最後に問題を受けた日用）
        latest_result = db.query(ExamResult).filter(
            ExamResult.user_id == current_user.id,
            ExamResult.exam_id == exam_id
        ).order_by(ExamResult.timestamp.desc()).first()

        # 最初の合格結果を取得（合格日時用）
        first_pass_result = db.query(ExamResult).filter(
            ExamResult.user_id == current_user.id,
            ExamResult.exam_id == exam_id,
            ExamResult.correct_count == ExamResult.total_questions
        ).order_by(ExamResult.timestamp.asc()).first()

        if latest_result:
            # 一度でも合格したことがあれば永久に合格
            if first_pass_result:
                status = 'pass'
            else:
                status = 'fail'

            exam_statuses.append({
                'exam_id': exam_id,
                'exam_title': exam_title,
                'status': status,
                'correct_count': latest_result.correct_count,
                'total_questions': latest_result.total_questions,
                'last_attempt': latest_result.timestamp,
                'pass_date': first_pass_result.timestamp if first_pass_result else None
            })
        else:
            # 未実施
            exam_statuses.append({
                'exam_id': exam_id,
                'exam_title': exam_title,
                'status': 'not_taken',
                'correct_count': None,
                'total_questions': None,
                'last_attempt': None,
                'pass_date': None
            })

    # exam_idでソート
    exam_statuses.sort(key=lambda x: x['exam_id'])

    return templates.TemplateResponse("mypage.html", {
        "request": request,
        "current_user": current_user,
        "exam_statuses": exam_statuses
    })

# 管理者ダッシュボード（メニュー）
@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    current_user: User = Depends(get_current_user)
    ):
    require_admin(current_user)
    return templates.TemplateResponse("admin.html", {"request": request})

# ユーザー一覧ページ
@app.get("/admin/users", response_class=HTMLResponse)
async def admin_users_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
    ):
    require_admin(current_user)
    
    users = db.query(User).join(Organization, User.organization_id == Organization.id).filter(User.deleted_at.is_(None)).order_by(User.created_at.desc()).all()
    
    # 各ユーザーの受講状況を計算
    user_statuses = []
    for user in users:
        total_exams = len(exam_data)
        pass_count = 0
        
        for exam_id in exam_data.keys():
            # ユーザーの合格結果を取得（一度でも合格していればカウント）
            pass_result = db.query(ExamResult).filter(
                ExamResult.user_id == user.id,
                ExamResult.exam_id == exam_id,
                ExamResult.correct_count == ExamResult.total_questions
            ).first()
            
            if pass_result:
                pass_count += 1
        
        # 受講状況を判定
        if pass_count == total_exams:
            status = "修了"
        else:
            status = "受講中"
            
        user_statuses.append({
            'user': user,
            'status': status,
            'pass_count': pass_count,
            'total_exams': total_exams
        })
    
    return templates.TemplateResponse("admin_users.html", {
        "request": request,
        "user_statuses": user_statuses
    })

# ユーザー登録ページ
@app.get("/admin/register", response_class=HTMLResponse)
async def register_page(
    request: Request,
    register_error: Optional[str] = Query(None),
    register_success: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
    ):
    require_admin(current_user)

    # 組織一覧を取得
    organizations = get_all_organizations()
    
    return templates.TemplateResponse("admin_register.html", {
        "request": request,
        "register_error": register_error,
        "register_success": register_success,
        "organizations": organizations
    })

# ユーザー登録処理
@app.post("/admin/register")
async def register_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    organization: str = Form(...),
    is_admin: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
    ):
    require_admin(current_user)

    # バリデーションチェック
    if error_msg := validate_registration(email, password, confirm_password, first_name, last_name, db):
        return redirect_with_message(error_msg)

    try:
        # 組織IDを取得
        organization_obj = db.query(Organization).filter(Organization.name == organization).first()
        if not organization_obj:
            return redirect_with_message(f"組織「{organization}」が見つかりません")
            
        # ユーザー作成
        is_admin_bool = is_admin.lower() == 'true'
        new_user = User(
            username=email,  # メールアドレスをユーザー名として使用
            email=email,
            first_name=first_name,
            last_name=last_name,
            organization_id=organization_obj.id,
            hashed_password=get_password_hash(password), 
            is_admin=is_admin_bool
        )
        db.add(new_user)
        db.commit()
        
        logger.info(f"User registered: {email} ({last_name} {first_name}) by {current_user.email}")
        return redirect_with_message(f"ユーザー「{last_name} {first_name}」を登録しました", is_error=False)
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return redirect_with_message("登録中にエラーが発生しました")

# 受験履歴ページ
@app.get("/admin/history", response_class=HTMLResponse)
async def admin_history_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
    ):
    require_admin(current_user)

    # 全ての受験履歴を最新順で取得
    results = db.query(ExamResult).join(User).filter(User.deleted_at.is_(None)).order_by(ExamResult.timestamp.desc()).all()

    return templates.TemplateResponse("admin_history.html", {
        "request": request,
        "results": results
    })

# パスワード変更ページ
@app.get("/admin/users/{user_id}/change-password", response_class=HTMLResponse)
def change_password_page(
    user_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
    ):
    require_admin(current_user)
    
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
    
    return templates.TemplateResponse("admin_change_password.html", {
        "request": request,
        "current_user": current_user,
        "target_user": target_user
    })

# パスワード変更処理
@app.post("/admin/users/{user_id}/change-password")
def change_password(
    user_id: int,
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
    ):
    require_admin(current_user)
    
    if new_password != confirm_password:
        return RedirectResponse(url=f"/admin/users/{user_id}/change-password?error=password_mismatch", status_code=302)
    
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")

    target_user.hashed_password = get_password_hash(new_password)
    db.commit()
    
    return RedirectResponse(url="/admin/users?success=password_changed", status_code=302)

# ユーザー削除処理
@app.delete("/api/admin/users/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
    ):
    require_admin(current_user)
    
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
    
    # 自分自身は削除できないようにする
    if target_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="自分自身は削除できません")
    
    # 管理者ユーザーは削除できないようにする
    if target_user.is_admin:
        raise HTTPException(status_code=400, detail="管理者ユーザーは削除できません")
    
    # 既に削除されているかチェック
    if target_user.deleted_at is not None:
        raise HTTPException(status_code=400, detail="既に削除されています")
    
    # 論理削除（deleted_atに現在時刻を設定）
    target_user.deleted_at = datetime.utcnow()
    db.commit()
    
    return {"message": "ユーザーを削除しました", "user_id": user_id}
