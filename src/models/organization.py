from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from .database import Base

class Organization(Base):
    """事業部モデル"""
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    
    users = relationship("User", back_populates="organization_rel")
