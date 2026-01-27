from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from models.database import Base


class User(Base):
    """ユーザーモデル"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String)
    role_id = Column(Integer, ForeignKey("roles.id"), default=1)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    exam_results = relationship("ExamResult", back_populates="user")
    organization_rel = relationship("Organization", back_populates="users")
    role = relationship("Role", back_populates="users")
    
    @property
    def is_admin(self) -> bool:
        """管理者か"""
        return self.role_id == 0
    
    @property
    def can_manage(self) -> bool:
        """運用者か"""
        return self.role_id in [0, 2]
