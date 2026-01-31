from sqlalchemy.orm import Session
from fastapi import Depends

from models.role import Role
from models.database import get_db


class RoleRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, role_id: int) -> Role | None:
        """指定IDのロールを取得"""
        return self.db.query(Role).filter(Role.id == role_id).first()
    
    def get_all(self) -> list[Role]:
        """全ロールを取得"""
        return self.db.query(Role).all()


def get_role_repository(db: Session = Depends(get_db)) -> RoleRepository:
    return RoleRepository(db)
