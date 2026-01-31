import bcrypt
import hashlib

from fastapi import Depends

from models.user import User
from repositories.user import UserRepository, get_user_repository


class AuthService:
    """認証サービス"""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """パスワードを検証"""
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    def hash_password(self, password: str) -> str:
        """パスワードをハッシュ化"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def authenticate(self, email: str, password: str) -> User | None:
        """ユーザー認証"""
        user = self.user_repository.get_by_email(email)
        if not user:
            return None
        
        if not self.verify_password(password, user.hashed_password):
            return None
        
        return user
    
    def generate_login_hash(self, user: User) -> str:
        """ログインハッシュを生成（Cookie改ざん防止）"""
        return hashlib.sha256(f"{user.id}{user.email}{user.hashed_password}".encode()).hexdigest()
    
    def verify_login_hash(self, user: User, login_hash: str) -> bool:
        """ログインハッシュを検証"""
        expected_hash = self.generate_login_hash(user)
        return login_hash == expected_hash
    
    def get_current_user(self, email: str | None, login_hash: str | None) -> User | None:
        """現在のユーザーを取得（Cookie検証含む）"""
        if not email or not login_hash:
            return None
        
        user = self.user_repository.get_by_email(email)
        if not user:
            return None
        
        if not self.verify_login_hash(user, login_hash):
            return None
        
        return user


def get_auth_service(
    user_repository: UserRepository = Depends(get_user_repository)
) -> AuthService:
    return AuthService(user_repository)
