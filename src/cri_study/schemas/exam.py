from pydantic import BaseModel


class Answer(BaseModel):
    """試験の回答"""

    question_id: int
    selected_option: int


class SubmitExamRequest(BaseModel):
    """試験提出リクエスト"""

    answers: list[Answer]
