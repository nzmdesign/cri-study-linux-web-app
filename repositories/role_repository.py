from sqlalchemy.orm import Session
from models.role import Role

class RoleRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self) -> list[Role]:
        """すべてのロールを取得"""
        return self.db.query(Role).all()
