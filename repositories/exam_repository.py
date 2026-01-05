from sqlalchemy.orm import Session
from models.exam import ExamResult

class ExamRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_user_and_exam(self, user_id: int, exam_id: int, result_id: int) -> ExamResult | None:
        """ユーザーIDと試験IDと結果IDで試験結果を取得"""
        return self.db.query(ExamResult).filter(
            ExamResult.id == result_id,
            ExamResult.user_id == user_id,
            ExamResult.exam_id == exam_id
        ).first()
    
    def get_latest_by_user_and_exam(self, user_id: int, exam_id: int) -> ExamResult | None:
        """ユーザーの特定試験の最新結果を取得"""
        return self.db.query(ExamResult).filter(
            ExamResult.user_id == user_id,
            ExamResult.exam_id == exam_id
        ).order_by(ExamResult.timestamp.desc()).first()
    
    def get_first_pass_by_user_and_exam(self, user_id: int, exam_id: int) -> ExamResult | None:
        """ユーザーの特定試験の初回合格結果を取得"""
        return self.db.query(ExamResult).filter(
            ExamResult.user_id == user_id,
            ExamResult.exam_id == exam_id,
            ExamResult.correct_count == ExamResult.total_questions
        ).order_by(ExamResult.timestamp.asc()).first()
    
    def get_all(self) -> list[ExamResult]:
        """全試験結果を取得"""
        return self.db.query(ExamResult).order_by(ExamResult.timestamp.desc()).all()
    
    def create(self, exam_result: ExamResult) -> ExamResult:
        """新規試験結果を作成"""
        self.db.add(exam_result)
        self.db.commit()
        self.db.refresh(exam_result)
        return exam_result
