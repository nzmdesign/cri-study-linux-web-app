from unittest.mock import MagicMock, patch
from repositories.role import RoleRepository, get_role_repository


class TestRoleRepositoryGetById:
    """RoleRepository.get_by_id のテスト"""

    def test_returns_role_when_exists(self):
        """IDで検索して、ロールが存在する場合、そのロールを返す"""
        mock_db = MagicMock()
        mock_role = MagicMock()
        
        # クエリチェーンをモック
        mock_db.query.return_value.filter.return_value.first.return_value = mock_role
        
        repo = RoleRepository(mock_db)
        result = repo.get_by_id(1)
        
        assert result == mock_role
        mock_db.query.assert_called_once()

    def test_returns_none_when_not_exists(self):
        """IDで検索して、ロールが存在しない場合、Noneを返す"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        repo = RoleRepository(mock_db)
        result = repo.get_by_id(1)
        
        assert result is None
        mock_db.query.assert_called_once()


class TestRoleRepositoryGetAll:
    """RoleRepository.get_all のテスト"""

    def test_returns_roles_list(self):
        """全ロールを取得できることを確認する"""
        mock_db = MagicMock()
        mock_roles = [MagicMock(), MagicMock()]
        mock_db.query.return_value.all.return_value = mock_roles
        
        repo = RoleRepository(mock_db)
        result = repo.get_all()
        
        assert result == mock_roles
        assert len(result) == 2
        mock_db.query.assert_called_once()

    def test_returns_empty_list_when_no_roles(self):
        """ロールが存在しない場合、空リストを返す"""
        mock_db = MagicMock()
        mock_db.query.return_value.all.return_value = []
        
        repo = RoleRepository(mock_db)
        result = repo.get_all()
        
        assert result == []
        mock_db.query.assert_called_once()

class TestGetRoleRepository:
    """get_role_repository 関数のテスト"""
    
    def test_returns_role_repository_instance(self):
        """RoleRepository インスタンスを返すことを確認"""
        mock_db = MagicMock()
        result = get_role_repository(mock_db)
        
        assert isinstance(result, RoleRepository)
        assert result.db == mock_db
        mock_db.assert_not_called()