"""テスト用の共通設定とフィクスチャ"""
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# プロジェクトパスを追加
project_root = Path(__file__).parent.parent / "src" / "cri_study"
sys.path.insert(0, str(project_root))

from database import Base


@pytest.fixture(scope="session")
def test_db_engine():
    """テスト用インメモリデータベース"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def test_db_session(test_db_engine):
    """テスト用セッション"""
    TestSessionLocal = sessionmaker(bind=test_db_engine)
    session = TestSessionLocal()
    
    yield session
    
    session.rollback()
    session.close()


@pytest.fixture
def test_container():
    """テスト用DIコンテナ
    
    実際のサービスとリポジトリの依存性を注入できる
    """
    from models.user import User
    from models.role import Role
    
    container = {
        "db": None,  # test_db_session で上書き
        "services": {},
        "repositories": {},
        "mocks": {},
    }
    
    return container


@pytest.fixture
def app_override_dependencies():
    """FastAPI アプリケーションの依存性上書き用フィクスチャ
    
    使用例:
        def test_example(app_override_dependencies):
            from fastapi.testclient import TestClient
            from main import app
            from services.auth import AuthService
            
            mock_auth_service = Mock(spec=AuthService)
            app_override_dependencies(
                "auth_service",
                mock_auth_service
            )
            
            client = TestClient(app)
            response = client.get("/")
    """
    overrides = {}
    
    def override(key: str, value):
        """依存性を上書き"""
        overrides[key] = value
    
    return override, overrides
