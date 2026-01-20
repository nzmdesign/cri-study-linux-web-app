from sqlalchemy.orm import Session
from models.user import User
from models.role import Role
from models.organization import Organization
from repositories.user_repository import UserRepository
from repositories.organization_repository import OrganizationRepository
from services.auth_service import AuthService

class UserService:
    """ユーザーサービス"""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        self.organization_repository = OrganizationRepository(db)
        self.auth_service = AuthService(db)
    
    def get_all_users(self) -> list[User]:
        """全ユーザーを取得"""
        return self.user_repository.get_all()
    
    def get_user_by_id(self, user_id: int) -> User | None:
        """IDでユーザーを取得"""
        return self.user_repository.get_by_id(user_id)
    
    def create_user(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        organization_name: str,
        role_id: int = 1
    ) -> User:
        """新規ユーザーを作成"""
        organization = self.organization_repository.get_by_name(organization_name)
        
        # ユーザーを作成
        user = User(
            username=email,
            email=email,
            first_name=first_name,
            last_name=last_name,
            organization_id=organization.id,
            hashed_password=self.auth_service.hash_password(password),
            role_id=role_id
        )
        
        return self.user_repository.create(user)
    
    def update_password(self, user_id: int, new_password: str) -> User | None:
        """ユーザーのパスワードを更新"""
        user = self.user_repository.get_by_id(user_id)
        if not user:
            return None
        
        user.hashed_password = self.auth_service.hash_password(new_password)
        return self.user_repository.update(user)
    
    def update_user_role(self, user_id: int, role_id: int) -> User | None:
        """ユーザーのロールを更新"""
        return self.user_repository.update_role(user_id, role_id)
    
    def delete_user(self, user_id: int, current_user_id: int) -> str | None:
        """ユーザーを物理削除（エラーコードを返す）"""
        user = self.user_repository.get_by_id(user_id)
        if not user:
            return "user_not_found"
        if user.id == current_user_id:
            return "cannot_delete_self"
        if user.is_admin:
            return "cannot_delete_admin"
        
        self.user_repository.delete(user)
        return None
    
    def validate_registration(
        self,
        email: str,
        password: str,
        confirm_password: str,
        first_name: str,
        last_name: str,
        organization_name: str
    ) -> str | None:
        """ユーザー登録のバリデーション（エラーコードを返す）"""
        if password != confirm_password:
            return "パスワードが一致しません"
        if len(password) < 4:
            return "パスワードは4文字以上で入力してください"
        if self.user_repository.exists_by_email(email):
            return "このメールアドレスは既に登録されています"
        if not self.organization_repository.get_by_name(organization_name):
            return "指定された所属が見つかりません"
        return None
