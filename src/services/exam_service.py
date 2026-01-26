import json
from pathlib import Path
from sqlalchemy.orm import Session
from models.exam import ExamResult
from repositories.exam_repository import ExamRepository
from utils.datetime_utils import to_jst

class ExamService:
    """試験サービス"""
    
    def __init__(self, db: Session):
        self.db = db
        self.exam_repository = ExamRepository(db)
        self.exam_data = self._load_exam_data()
    
    def _load_exam_data(self) -> dict:
        """試験データをJSONファイルから読み込み"""
        base_dir = Path(__file__).parent.parent
        exam_dir = base_dir / "content" / "exam"
        exams = {}
        
        if not exam_dir.exists() or not exam_dir.is_dir():
            raise FileNotFoundError("content/exam ディレクトリが存在しません。必ず作成してください。")
        
        for exam_file in sorted(exam_dir.glob("*.json")):
            try:
                exam_id = int(exam_file.stem)
            except Exception:
                continue
            
            try:
                with open(exam_file, "r", encoding="utf-8") as f:
                    exam_data = json.load(f)
                    exams[exam_id] = exam_data
            except Exception:
                print(f"警告: {exam_file} の読み込みに失敗しました")
                continue
        
        return exams
    
    def get_exam_data(self, exam_id: int) -> dict | None:
        """試験データを取得"""
        return self.exam_data.get(exam_id)
    
    def get_all_exam_ids(self) -> list[int]:
        """全試験IDを取得"""
        return list(self.exam_data.keys())
    
    def submit_exam(self, user_id: int, exam_id: int, answers: list[dict]) -> ExamResult:
        """試験を採点して結果を保存"""
        exam = self.get_exam_data(exam_id)
        if not exam:
            raise ValueError("試験が見つかりません")
        
        questions = exam["questions"]
        
        # 採点処理
        correct_count = 0
        for question in questions:
            for answer in answers:
                if answer["question_id"] == question["id"]:
                    if answer["selected_option"] == question["correct"]:
                        correct_count += 1
                    break
        
        # 結果を保存
        exam_result = ExamResult(
            user_id=user_id,
            exam_id=exam_id,
            exam_title=exam["title"],
            correct_count=correct_count,
            total_questions=len(questions)
        )
        
        return self.exam_repository.create(exam_result)
    
    def get_exam_result(self, user_id: int, exam_id: int, result_id: int) -> ExamResult | None:
        """試験結果を取得"""
        result = self.exam_repository.get_by_user_and_exam(user_id, exam_id, result_id)
        if result:
            result.timestamp = to_jst(result.timestamp)
        return result
    
    def get_user_exam_statuses(self, user_id: int) -> list[dict]:
        """ユーザーの全試験の受験状況を取得"""
        exam_statuses = []
        
        for exam_id in self.get_all_exam_ids():
            exam_title = self.exam_data[exam_id]["title"]
            
            # 最新の受験結果を取得
            latest_result = self.exam_repository.get_latest_by_user_and_exam(user_id, exam_id)
            
            # 最初の合格結果を取得
            first_pass_result = self.exam_repository.get_first_pass_by_user_and_exam(user_id, exam_id)
            
            if latest_result:
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
                    'last_attempt': to_jst(latest_result.timestamp),
                    'pass_date': to_jst(first_pass_result.timestamp) if first_pass_result else None
                })
            else:
                exam_statuses.append({
                    'exam_id': exam_id,
                    'exam_title': exam_title,
                    'status': 'not_taken',
                    'correct_count': None,
                    'total_questions': None,
                    'last_attempt': None,
                    'pass_date': None
                })
        
        exam_statuses.sort(key=lambda x: x['exam_id'])
        return exam_statuses
    
    def get_all_results(self) -> list[ExamResult]:
        """全試験結果を取得"""
        all_results = []
        for result in self.exam_repository.get_all():
            result.timestamp = to_jst(result.timestamp)
            all_results.append(result)
        return all_results
    
    def calculate_user_progress(self, user_id: int) -> dict:
        """ユーザーの受講進捗を計算"""
        total_exams = len(self.exam_data)
        pass_count = 0
        
        for exam_id in self.get_all_exam_ids():
            pass_result = self.exam_repository.get_first_pass_by_user_and_exam(user_id, exam_id)
            if pass_result:
                pass_count += 1
        
        status = "修了" if pass_count == total_exams else "受講中"
        
        return {
            'status': status,
            'pass_count': pass_count,
            'total_exams': total_exams
        }
