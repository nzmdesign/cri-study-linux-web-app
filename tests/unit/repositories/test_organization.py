from unittest.mock import MagicMock
from repositories.organization import OrganizationRepository, get_organization_repository


class TestOrganizationRepositoryGetByName:
    """OrganizationRepository.get_by_name のテスト"""

    def test_returns_organization_when_exists(self):
        """名前で検索して、事業部が存在する場合、その事業部を返す"""
        mock_db = MagicMock()
        mock_organization = MagicMock()
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_organization
        
        repo = OrganizationRepository(mock_db)
        result = repo.get_by_name("Test Organization")
        
        assert result == mock_organization
        mock_db.query.assert_called_once()

    def test_returns_none_when_not_exists(self):
        """名前で検索して、事業部が存在しない場合、Noneを返す"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        repo = OrganizationRepository(mock_db)
        result = repo.get_by_name("Nonexistent Organization")
        
        assert result is None
        mock_db.query.assert_called_once()


class TestOrganizationRepositoryGetAll:
    """OrganizationRepository.get_all のテスト"""

    def test_returns_organizations_list(self):
        """全事業部を取得できることを確認する"""
        mock_db = MagicMock()
        mock_organizations = [MagicMock(), MagicMock()]
        mock_db.query.return_value.order_by.return_value.all.return_value = mock_organizations
        
        repo = OrganizationRepository(mock_db)
        result = repo.get_all()
        
        assert result == mock_organizations
        assert len(result) == 2
        mock_db.query.assert_called_once()

    def test_returns_empty_list_when_no_organizations(self):
        """事業部が存在しない場合、空リストを返す"""
        mock_db = MagicMock()
        mock_db.query.return_value.order_by.return_value.all.return_value = []
        
        repo = OrganizationRepository(mock_db)
        result = repo.get_all()
        
        assert result == []
        mock_db.query.assert_called_once()

class TestGetOrganizationRepository:
    """get_organization_repository 関数のテスト"""
    
    def test_returns_organization_repository_instance(self):
        """OrganizationRepository インスタンスを返すことを確認"""
        mock_db = MagicMock()
        result = get_organization_repository(mock_db)
        
        assert isinstance(result, OrganizationRepository)
        assert result.db == mock_db
        mock_db.assert_not_called()