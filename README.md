# CRI Study Linux Web Application

## セットアップ

### 1. 設定ファイルの作成

アプリケーションを初回起動する前に、管理者ユーザーの設定ファイルを作成してください。

```bash
cp config.json.template config.json
```

### 2. 管理者情報の設定

`config.json`ファイルを編集して、管理者ユーザーの情報を設定してください：

```json
{
  "admin_user": {
    "email": "your-admin@example.com",
    "first_name": "あなたの名前",
    "last_name": "あなたの姓",
    "organization": "あなたの所属組織",
    "password": "secure_password_123"
  }
}
```

**重要**: 
- `email`: 管理者のメールアドレス（ログインに使用）
- `password`: 安全なパスワードを設定してください
- すべてのフィールドが必須です

### 3. アプリケーションの起動

```bash
python main.py
```

初回起動時に、設定ファイルから管理者ユーザーが自動作成されます。

### 4. ログイン

設定したメールアドレスとパスワードでログインしてください。

## セキュリティ

- `config.json`ファイルは機密情報を含むため、バージョン管理には含まれません
- 本番環境では強固なパスワードを設定してください
- 定期的にパスワードを変更することを推奨します