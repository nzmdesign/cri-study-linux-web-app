# CRI Study Linux Web App

本リポジトリは「CRI Study Linux Web App」のソースコードを管理するリポジトリである。

## アプリ構成
- フロントエンド: Jina2 + htmx + Tailwind CSS
- バックエンド: Python3.11 + FastAPI
- Webサーバ（リバプロ）: Nginx
- データベース: SQLite

## データベースについて
SQLiteを使用しているため、単一のファイルでデータベースが管理されている。
ファイルは`/var/www/cri-study-linux-web-app/src/cri_study/app.db`に配置されている。このファイルはsystemd.timerを使用して定期的にS3バケットへバックアップしている。

## ヘルスチェックについて
Route53のヘルスチェックでtcp/80を使用しているため、正常な応答を返さない場合はRoute53でトラフィックをCloudFrontへフェイルオーバする。
アプリケーションのヘルスチェックエンドポイントは`/health`で実装されているが使用していない。

## 夜間停止について
コスト削減のため、EC2インスタンスは夜間に停止するようにEvent Bridge ScedulerとStep Functionsで設定している。夜間停止中はヘルスチェックが失敗するため、Route53でトラフィックをCloudFrontへフェイルオーバする。停止期間を変更したい場合は、IaCリポジトリ（`cri-study-linux-web-app-infra`）の設定を変更すること。

## デプロイ方法
デプロイはGitHub Actionsで自動化している。ワークフローは`.github/workflows/deploy.yml`で定義している。

### GitHub Actionsへの変数登録
リポジトリのGitHub Actionsに以下の変数とシークレットを登録する。
- IaCリポジトリ（`cri-study-linux-web-app-infra`）の手順で作成したSSHキーペアの秘密鍵
- アプリの管理者ユーザーの初期パスワード（例: `Admin!123`）
- 取得したEC2インスタンスのホスト名（ドメイン名）
- デプロイ用のユーザ名`deploy`
- Terraformで作成したフォールバック用のページを置くS3バケット名（例: `{ACCOUNT_ID}-cri-study-linux-prod-failover-site`）

手順は以下の通り。
1. GitHubリポジトリのSettings > Secrets and variables > Actionsに移動する。
2. Secretsタブで「New repository secret」をクリックする。
3. `Name`に`DEPLOY_KEY`と入力し、`Value`にSSHキーペアの秘密鍵をペーストして「Add secret」をクリックする。
4. `Name`に`ADMIN_INITIAL_PASSWORD`と入力し、`Value`にアプリの管理者ユーザーの初期パスワードを入力して「Add variable」をクリックする。
5. Variablesタブで「New repository variable」をクリックする。
6. `Name`に`EC2_HOSTNAME`と入力し、`Value`にEC2インスタンスのホスト名（ドメイン名）を入力して「Add variable」をクリックする。
7. `Name`に`DEPLOY_USERNAME`と入力し、`Value`に`deploy`を入力して「Add variable」をクリックする。
8. `Name`に`FALLBACK_S3_BUCKET`と入力し、`Value`にTerraformで作成したフォールバック用のページを置くS3バケット名（例: `{ACCOUNT_ID}-cri-study-linux-prod-failover-site`）を入力して「Add variable」をクリックする。

### コンフィグファイルの変更
デプロイ前に、必要に応じて`src/cri_study/config.json.template`をコピーして`src/cri_study/config.json`を作成し、設定を変更すること。
`github_repo_url`はカリキュラム用のテキストファイルを配置しているリポジトリのURLを指定する（例: `https://github.com/xnterada/cri-study-linux-web-app-text`）

### デプロイの実行
（注意）EC2インスタンスが起動していること。
mainブランチに変更をマージ・プッシュすると、GitHub Actionsが自動的にデプロイを実行する。デプロイの進行状況はGitHub Actionsのワークフローで確認できる。
ワークフロー定義は`.github/workflows/deploy.yml`にある。
`workflow_dispatch`トリガーも設定しているため、GitHub ActionsのUIから手動でデプロイを実行することも可能。

### 各サービスの動作確認

EC2インスタンスにSSMまたはSSHで接続して以下のコマンドを実行する。以下はfastapi_appの例。
```bash
sudo systemctl status fastapi_app
```

問題がある場合はjournalctlでジャーナルログを確認する。以下はfastapi_appの例。
```bashbash
sudo journalctl -u fastapi_app -n 50 --no-pager
```

### DBリストア
バックアップされたDBファイルはS3バケットに保存されている。リストアの手順を以下に示す。
```bash
# S3からバックアップファイルをダウンロード
cd /var/www/cri-study-linux-web-app/src/cri_study
aws s3 cp <DBバックアップのS3オブジェクトパス> .
# 既存のDBファイルをリストアしたファイルに置き換える（サービスを停止すること）
sudo systemctl stop fastapi_app
mv app.db app.db.bak
mv <ダウンロードしたバックアップファイル名> app.db
sudo systemctl start fastapi_app
```
