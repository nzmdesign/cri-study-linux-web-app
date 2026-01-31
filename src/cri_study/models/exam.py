from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from models.database import Base


class ExamResult(Base):
    """試験結果モデル"""
    __tablename__ = "exam_results"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    exam_id = Column(Integer)
    exam_title = Column(String)
    correct_count = Column(Integer)
    total_questions = Column(Integer)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="exam_results")
