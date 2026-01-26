from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import BaseModel
from models.database import get_db
from models.user import User
from services.exam_service import ExamService
from src.routers.auth_router import get_current_user
import os

router = APIRouter()
templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
templates = Jinja2Templates(directory=templates_dir)

class Answer(BaseModel):
    question_id: int
    selected_option: int

class SubmitExamRequest(BaseModel):
    answers: list[Answer]

@router.get("/exam/{exam_id}", response_class=HTMLResponse)
async def exam_page(
    request: Request,
    exam_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """試験ページ"""
    if not current_user:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url='/login', status_code=302)
    
    exam_service = ExamService(db)
    exam = exam_service.get_exam_data(exam_id)
    
    if not exam:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "message": "試験が見つかりません"
        })
    
    return templates.TemplateResponse("exam.html", {
        "request": request,
        "exam": exam,
        "exam_id": exam_id,
        "current_user": current_user
    })

@router.post("/exam/{exam_id}/submit")
async def submit_exam_form(
    request: Request,
    exam_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """フォームからの試験提出"""
    if not current_user:
        return RedirectResponse(url='/login', status_code=302)
    
    # フォームデータを取得
    form_data = await request.form()
    
    exam_service = ExamService(db)
    exam = exam_service.get_exam_data(exam_id)
    
    if not exam:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "message": "試験が見つかりません"
        })
    
    # フォームデータから回答を抽出
    answers = []
    for question in exam["questions"]:
        field_name = f"answer_{question['id']}"
        if field_name in form_data:
            answers.append({
                "question_id": question['id'],
                "selected_option": int(form_data[field_name])
            })
    
    try:
        exam_result = exam_service.submit_exam(current_user.id, exam_id, answers)
        return RedirectResponse(
            url=f"/exam/{exam_id}/result/{exam_result.id}",
            status_code=303
        )
    except ValueError as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "message": str(e)
        }, status_code=400)

@router.post("/api/exam/{exam_id}/submit")
async def submit_exam(
    request: Request,
    exam_id: int,
    submit_data: SubmitExamRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """試験提出"""
    if not current_user:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "message": "認証が必要です"
        }, status_code=401)
    
    exam_service = ExamService(db)
    
    # 回答を辞書形式に変換
    answers = [{"question_id": a.question_id, "selected_option": a.selected_option} for a in submit_data.answers]
    
    try:
        exam_result = exam_service.submit_exam(current_user.id, exam_id, answers)
        return {
            "result_id": exam_result.id,
            "redirect_url": f"/exam/{exam_id}/result/{exam_result.id}"
        }
    except ValueError as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "message": str(e)
        }, status_code=400)

@router.get("/exam/{exam_id}/result/{result_id}", response_class=HTMLResponse)
async def exam_result_page(
    request: Request,
    exam_id: int,
    result_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """試験結果ページ"""
    if not current_user:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url='/login', status_code=302)
    
    exam_service = ExamService(db)
    exam_result = exam_service.get_exam_result(current_user.id, exam_id, result_id)
    
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

@router.get("/mypage", response_class=HTMLResponse)
async def mypage(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """マイページ"""
    if not current_user:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url='/login', status_code=302)
    
    exam_service = ExamService(db)
    exam_statuses = exam_service.get_user_exam_statuses(current_user.id)
    
    return templates.TemplateResponse("mypage.html", {
        "request": request,
        "current_user": current_user,
        "exam_statuses": exam_statuses
    })
