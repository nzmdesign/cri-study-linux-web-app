from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from models.database import Base


class Role(Base):
    """ロールモデル"""
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    
    users = relationship("User", back_populates="role")
