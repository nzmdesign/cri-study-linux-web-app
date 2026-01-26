from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    """ユーザーモデル"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)  # メールアドレス
    email = Column(String, unique=True, index=True)     # メールアドレス（usernameと同じ）
    first_name = Column(String)                         # 名
    last_name = Column(String)                          # 姓
    hashed_password = Column(String)
    role_id = Column(Integer, ForeignKey("roles.id"), default=1)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    exam_results = relationship("ExamResult", back_populates="user")
    organization_rel = relationship("Organization", back_populates="users")
    role = relationship("Role", back_populates="users")
    
    @property
    def is_admin(self) -> bool:
        """管理者か"""
        return self.role_id == 0
    
    @property
    def is_operator(self) -> bool:
        """運用者か"""
        return self.role_id == 2
    
    @property
    def can_manage(self) -> bool:
        """管理可能か"""
        return self.role_id in [0, 2]
