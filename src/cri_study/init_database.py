import bcrypt
import json
import os
import sys
from pathlib import Path

from models.database import SessionLocal, create_tables
from models.organization import Organization
from models.role import Role
from models.user import User


def load_config():
    """設定ファイルを読み込む"""
    config_path = Path(__file__).parent / "config.json"
    if not config_path.exists():
        raise FileNotFoundError(f"設定ファイルが見つかりません: {config_path}")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"設定ファイルの形式が正しくありません: {e}") from e
    except IOError as e:
        raise IOError(f"設定ファイルの読み込みエラー: {e}") from e

def init_roles():
    """ロールを初期化"""
    try:
        config = load_config()
        roles_config = config.get("roles", [])

        if not roles_config:
            print("エラー: 設定ファイルに roles セクションが必要です")
            sys.exit(1)

    except (FileNotFoundError, ValueError, IOError) as e:
        print(f"設定ファイルの読み込みエラー: {e}")
        sys.exit(1)

    with SessionLocal() as db:
        try:
            for role_data in roles_config:
                role_id = role_data["id"]
                role_name = role_data["name"]

                existing_role = db.query(Role).filter(Role.id == role_id).first()
                if existing_role:
                    print(f"ロールは既に存在します: {role_name} (ID: {role_id})")
                    continue

                role = Role(id=role_id, name=role_name)
                db.add(role)
                print(f"ロールを作成しました: {role.name} (ID: {role.id})")

            db.commit()
        except KeyError as e:
            print(f"ロール設定に必須フィールドがありません: {e}")
            raise
        except Exception as e:
            print(f"ロール作成エラー: {e}")
            raise

def init_organizations():
    """事業部データを初期化"""

    try:
        config = load_config()
        organizations_config = config.get("organizations", [])

        if not organizations_config:
            print("エラー: 設定ファイルに organizations セクションが必要です")
            sys.exit(1)

    except (FileNotFoundError, ValueError, IOError) as e:
        print(f"設定ファイルの読み込みエラー: {e}")
        sys.exit(1)

    with SessionLocal() as db:
        try:
            for org_data in organizations_config:
                org_id = org_data["id"]
                org_name = org_data["name"]

                existing_org = db.query(Organization).filter(Organization.id == org_id).first()
                if existing_org:
                    print(f"事業部は既に存在します: {org_name} (ID: {org_id})")
                    continue

                organization = Organization(id=org_id, name=org_name)
                db.add(organization)
                print(f"事業部を作成しました: {org_name} (ID: {org_id})")

            db.commit()
        except KeyError as e:
            print(f"事業部設定に必須フィールドがありません: {e}")
            raise
        except Exception as e:
            print(f"事業部作成エラー: {e}")
            raise

def init_admin_user():
    """管理者ユーザーが存在しない場合は作成"""

    with SessionLocal() as db:
        # 管理者ユーザーが存在するかチェック
        exist_admin = db.query(User).filter(User.role_id == 0).first()
        if exist_admin:
            print(f"管理者ユーザーは既に存在します: {exist_admin.email}")
            return

        # 管理者ユーザーがいない場合のみconfigから読み取る
        try:
            config = load_config()
            admin_config = config.get("admin_user")

            if not admin_config:
                print("エラー: 設定ファイルに admin_user セクションが必要です")
                sys.exit(1)

            # 必須フィールドの確認
            required_fields = ["email", "first_name", "last_name", "organization_id"]
            missing_fields = [
                field for field in required_fields 
                if admin_config.get(field) is None or admin_config.get(field) == ""
            ]

            if missing_fields:
                print(f"エラー: 設定ファイルに必須フィールドが不足しています: {', '.join(missing_fields)}")
                sys.exit(1)

        except (FileNotFoundError, ValueError, IOError) as e:
            print(f"設定ファイルの読み込みエラー: {e}")
            sys.exit(1)

        # 管理者ユーザーを作成
        try:
            admin_password = os.environ.get("ADMIN_INITIAL_PASSWORD")
            if not admin_password:
                print("警告: ADMIN_INITIAL_PASSWORD が未設定のため管理者ユーザーの作成をスキップします")
                return
            hashed_password = bcrypt.hashpw(admin_password.encode("utf-8"), bcrypt.gensalt())
            admin_user = User(
                username=admin_config["email"],
                email=admin_config["email"],
                first_name=admin_config["first_name"],
                last_name=admin_config["last_name"],
                hashed_password=hashed_password.decode("utf-8"),
                organization_id=admin_config["organization_id"],
                role_id=0,
            )
            db.add(admin_user)
            db.commit()
            print(
                f"管理者ユーザーを作成しました: {admin_config['email']} "
                f"({admin_config['last_name']} {admin_config['first_name']})"
            )
        except KeyError as e:
            print(f"管理者ユーザー設定に必須フィールドがありません: {e}")
            raise
        except Exception as e:
            print(f"管理者ユーザー作成エラー: {e}")
            raise

def initialize_database():
    create_tables()
    init_roles()
    init_organizations()
    init_admin_user()
