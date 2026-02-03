import pytest
from unittest.mock import MagicMock
from fastapi import Request

from utils.auth import (
    ForbiddenException,
    UnauthenticatedException,
    require_authenticated,
    require_admin,
    require_manager,
    get_current_user
)

class TestExceptions:
    def test_unauthenticated_exception_is_exception(self):
        """UnauthenticatedExceptionがExceptionのサブクラスであることを確認する"""
        exc = UnauthenticatedException()
        assert isinstance(exc, Exception)

    def test_forbidden_exception_is_exception(self):
        """ForbiddenExceptionがExceptionのサブクラスであることを確認する"""
        exc = ForbiddenException()
        assert isinstance(exc, Exception)

class TestRequireAuthenticated:
    def test_raises_unauthenticated_exception_when_user_is_none(self):
        """ユーザーがNoneの場合、UnauthenticatedExceptionが発生することを確認する"""
        with pytest.raises(UnauthenticatedException):
            require_authenticated(current_user=None)

    def test_returns_user_when_user_is_not_none(self):
        """ユーザーが存在する場合、そのユーザーが返されることを確認する"""
        mock_user = MagicMock()
        result = require_authenticated(current_user=mock_user)
        assert result == mock_user

class TestRequireAdmin:
    def test_raises_unauthenticated_exception_when_user_is_none(self):
        """ユーザーがNoneの場合、UnauthenticatedExceptionが発生することを確認する"""
        with pytest.raises(UnauthenticatedException):
            require_admin(current_user=None)

    def test_raises_forbidden_exception_when_user_is_not_admin(self):
        """ユーザーが管理者でない場合、ForbiddenExceptionが発生することを確認する"""
        mock_user = MagicMock()
        mock_user.is_admin = False
        with pytest.raises(ForbiddenException):
            require_admin(current_user=mock_user)

    def test_returns_user_when_user_is_admin(self):
        """ユーザーが管理者の場合、そのユーザーが返されることを確認する"""
        mock_user = MagicMock()
        mock_user.is_admin = True
        result = require_admin(current_user=mock_user)
        assert result == mock_user

class TestRequireManager:
    def test_raises_unauthenticated_exception_when_user_is_none(self):
        """ユーザーがNoneの場合、UnauthenticatedExceptionが発生することを確認する"""
        with pytest.raises(UnauthenticatedException):
            require_manager(current_user=None)

    def test_raises_forbidden_exception_when_user_cannot_manage(self):
        """ユーザーが管理権限を持たない場合、ForbiddenExceptionが発生することを確認する"""
        mock_user = MagicMock()
        mock_user.can_manage = False
        with pytest.raises(ForbiddenException):
            require_manager(current_user=mock_user)

    def test_returns_user_when_user_can_manage(self):
        """ユーザーが管理権限を持つ場合、そのユーザーが返されることを確認する"""
        mock_user = MagicMock()
        mock_user.can_manage = True
        result = require_manager(current_user=mock_user)
        assert result == mock_user

class TestGetCurrentUser:
    def test_calls_auth_service_with_cookies(self):
        """Cookieからユーザー情報を取得することを確認"""
        mock_request = MagicMock(spec=Request)
        mock_request.cookies = {"user": "test@example.com", "login_hash": "hash123"}
        
        mock_auth_service = MagicMock()
        mock_auth_service.get_current_user.return_value = MagicMock()
        
        get_current_user(mock_request, mock_auth_service)
        
        mock_auth_service.get_current_user.assert_called_once_with(
            "test@example.com", "hash123"
        )
