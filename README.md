# CRI Study Linux Web App

FastAPI と SQLite を使用したWebアプリケーションです。

## デプロイについて

本アプリケーションのデプロイは GitHub Actions(`.github/workflows/deploy.yml`) によって自動化されています。
main ブランチへプッシュすると、EC2 インスタンスへのコード反映、ライブラリのインストール、および自動再起動が行われます。
