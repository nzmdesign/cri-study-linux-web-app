"""
SQLiteのexam_resultsテーブルにカスケード削除を適用するマイグレーションスクリプト
"""
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

DATABASE_URL = "sqlite:///./app.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# 外部キー制約を有効化
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def migrate():
    """exam_resultsテーブルをマイグレーション"""
    try:
        with engine.begin() as conn:
            # バックアップテーブルを作成
            print("バックアップを作成中...")
            conn.execute(text("CREATE TABLE exam_results_backup AS SELECT * FROM exam_results"))
            
            # 既存テーブルを削除
            print("既存テーブルを削除中...")
            conn.execute(text("DROP TABLE exam_results"))
            
            # 新しいテーブルを作成（カスケード削除付き）
            print("新しいテーブルを作成中...")
            conn.execute(text("""
                CREATE TABLE exam_results (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    exam_id INTEGER,
                    exam_title VARCHAR,
                    correct_count INTEGER,
                    total_questions INTEGER,
                    timestamp DATETIME,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """))
            
            # データを復元（user_idがNULLでないレコードのみ）
            print("データを復元中...")
            conn.execute(text("""
                INSERT INTO exam_results 
                SELECT * FROM exam_results_backup
                WHERE user_id IS NOT NULL
            """))
            
            # 削除されたユーザーのレコード数を確認
            result = conn.execute(text("""
                SELECT COUNT(*) FROM exam_results_backup
                WHERE user_id IS NULL
            """))
            deleted_count = result.scalar()
            if deleted_count > 0:
                print(f"⚠ 削除されたユーザーのレコード {deleted_count} 件をスキップしました")
            
            # バックアップテーブルを削除
            print("バックアップを削除中...")
            conn.execute(text("DROP TABLE exam_results_backup"))
            
            print("✓ マイグレーション完了しました")
            
    except Exception as e:
        print(f"✗ エラーが発生しました: {e}")
        raise


if __name__ == "__main__":
    print("SQLite マイグレーション開始")
    print("=" * 50)
    migrate()
    print("=" * 50)
