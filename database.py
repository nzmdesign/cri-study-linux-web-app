import bcrypt
import json
import os
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()

class Organization(Base):
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)      # 事業所名
    
    users = relationship("User", back_populates="organization_rel")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)  # メールアドレス
    email = Column(String, unique=True, index=True)     # メールアドレス（usernameと同じ）
    first_name = Column(String)                         # 名
    last_name = Column(String)                          # 姓
    organization_id = Column(Integer, ForeignKey("organizations.id"))  # 所属ID
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)  # 論理削除用フィールド

    exam_results = relationship("ExamResult", back_populates="user")
    organization_rel = relationship("Organization", back_populates="users")

class ExamResult(Base):
    __tablename__ = "exam_results"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    exam_id = Column(Integer)
    exam_title = Column(String)
    correct_count = Column(Integer)
    total_questions = Column(Integer)
    score_percentage = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(Text)  # 問題詳細のJSONデータ

    user = relationship("User", back_populates="exam_results")

# データベース設定
DATABASE_URL = "sqlite:///./app.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def load_config():
    """設定ファイルを読み込む"""
    config_path = "config.json"
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"設定ファイルが見つかりません: {config_path}")
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"設定ファイルの形式が正しくありません: {e}")
    except Exception as e:
        raise Exception(f"設定ファイルの読み込みエラー: {e}")

def create_tables():
    Base.metadata.create_all(bind=engine)

def init_organizations():
    """設定ファイルから初期組織を作成（存在しない場合）"""
    
    try:
        config = load_config()
        organizations_config = config.get("initial_organizations", [])
        
        if not organizations_config:
            print("警告: 設定ファイルに initial_organizations セクションが見つかりません")
            return
            
    except Exception as e:
        print(f"設定ファイルの読み込みエラー: {e}")
        return
    
    db = SessionLocal()
    try:
        for org_name in organizations_config:
            if not org_name:
                continue
                
            # 既存の組織をチェック
            existing_org = db.query(Organization).filter(Organization.name == org_name).first()
            if existing_org:
                print(f"組織は既に存在します: {org_name}")
                continue
                
            # 組織を作成
            organization = Organization(
                name=org_name
            )
            db.add(organization)
            print(f"組織を作成しました: {org_name}")
            
        db.commit()
        
    except Exception as e:
        print(f"組織の作成エラー: {e}")
        db.rollback()
    finally:
        db.close()

def init_admin_user():
    """設定ファイルから管理者ユーザーを作成（存在しない場合）"""
    
    try:
        config = load_config()
        admin_config = config.get("admin_user")
        
        if not admin_config:
            print("警告: 設定ファイルに admin_user セクションが見つかりません")
            return
            
        # 必須フィールドの確認
        required_fields = ["email", "first_name", "last_name", "organization", "password"]
        missing_fields = [field for field in required_fields if not admin_config.get(field)]
        
        if missing_fields:
            print(f"エラー: 設定ファイルに必須フィールドが不足しています: {', '.join(missing_fields)}")
            return
            
        admin_email = admin_config["email"]
        
    except Exception as e:
        print(f"設定ファイルの読み込みエラー: {e}")
        return
    
    db = SessionLocal()
    try:
        # 既存の管理者ユーザーをチェック
        existing_admin = db.query(User).filter(User.email == admin_email).first()
        if existing_admin:
            print(f"管理者ユーザーは既に存在します: {admin_email}")
            return
            
        # 組織IDを取得
        organization_name = admin_config["organization"]
        organization = db.query(Organization).filter(Organization.name == organization_name).first()
        if not organization:
            # 組織が存在しない場合は作成
            organization = Organization(name=organization_name)
            db.add(organization)
            db.flush()  # IDを取得するためにflush
            
        # 管理者ユーザーを作成
        hashed_password = bcrypt.hashpw(admin_config["password"].encode('utf-8'), bcrypt.gensalt())
        admin_user = User(
            username=admin_email,  # usernameにもemailを設定
            email=admin_email,
            first_name=admin_config["first_name"],
            last_name=admin_config["last_name"],
            organization_id=organization.id,
            hashed_password=hashed_password.decode('utf-8'),
            is_admin=True
        )
        db.add(admin_user)
        db.commit()
        print(f"管理者ユーザーを作成しました: {admin_email} ({admin_config['last_name']} {admin_config['first_name']})")
        
    except Exception as e:
        print(f"管理者ユーザーの作成エラー: {e}")
        db.rollback()
    finally:
        db.close()

def get_all_organizations():
    """すべての組織を取得"""
    db = SessionLocal()
    try:
        return db.query(Organization).order_by(Organization.name).all()
    finally:
        db.close()

def initialize_database():
    """データベースの初期化を実行"""
    create_tables()
    init_organizations()
    init_admin_user()
