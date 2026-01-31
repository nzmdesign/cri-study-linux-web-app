from sqlalchemy.orm import Session
from fastapi import Depends

from models.user import User
from models.database import get_db


class UserRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, user_id: int) -> User | None:
        """IDでユーザーを取得"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_email(self, email: str) -> User | None:
        """メールアドレスでユーザーを取得"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_all(self) -> list[User]:
        """全ユーザーを取得"""
        return self.db.query(User).order_by(User.created_at.desc()).all()
    
    def create(self, user: User) -> User:
        """新規ユーザーを作成"""
        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception:
            self.db.rollback()
            raise
    
    def update(self, user: User) -> User:
        """ユーザー情報を更新"""
        try:
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception:
            self.db.rollback()
            raise
    
    def delete(self, user: User) -> bool:
        """ユーザーを物理削除"""
        try:
            self.db.delete(user)
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            return False
    
    def update_role(self, user_id: int, role_id: int) -> User | None:
        """ユーザーのロールを更新"""
        user = self.get_by_id(user_id)
        if user:
            user.role_id = role_id
            return self.update(user)
        return None
    
    def exists_by_email(self, email: str) -> bool:
        """メールアドレスの存在確認"""
        return self.db.query(User.id).filter(User.email == email).first() is not None


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)
