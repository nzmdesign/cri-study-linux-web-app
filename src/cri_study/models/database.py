import os
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


db_path_str = os.getenv("DB_PATH")
if db_path_str is None:
    raise RuntimeError("環境変数 DB_PATH が設定されていません")
DB_PATH = Path(db_path_str)

DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_conn, connection_record):
    """SQLiteで外部キー制約を有効化"""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """DBセッション取得（FastAPI Depends用）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """全テーブルを作成"""
    Base.metadata.create_all(bind=engine)
