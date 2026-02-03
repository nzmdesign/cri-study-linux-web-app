from fastapi import Depends, Request

from models.user import User
from services.auth import AuthService, get_auth_service


class UnauthenticatedException(Exception):
    """未認証例外"""
    pass


class ForbiddenException(Exception):
    """権限不足例外"""
    pass


def get_current_user(
    request: Request, auth_service: AuthService = Depends(get_auth_service)
) -> User | None:
    """Cookieから現在のユーザーを取得
    
    DIパターンを使用しており、テスト時は auth_service をモックに差し替え可能
    """
    email = request.cookies.get("user")
    login_hash = request.cookies.get("login_hash")

    return auth_service.get_current_user(email, login_hash)


def require_authenticated(current_user: User | None = Depends(get_current_user)) -> User:
    """ログイン済みユーザー認証"""
    if not current_user:
        raise UnauthenticatedException()
    return current_user


def require_admin(current_user: User | None = Depends(get_current_user)) -> User:
    """ログイン済みユーザー認証と管理者権限をチェックする"""
    if not current_user:
        raise UnauthenticatedException()
    if not current_user.is_admin:
        raise ForbiddenException()
    return current_user


def require_manager(current_user: User | None = Depends(get_current_user)) -> User:
    """ログイン済みユーザー認証と管理権限をチェックする"""
    if not current_user:
        raise UnauthenticatedException()
    if not current_user.can_manage:
        raise ForbiddenException()
    return current_user
