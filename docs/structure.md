# リポジトリ構成 / フォルダ・ファイル説明

このプロジェクトは「検証（scripts）→ サーバ統合（app）」の順に拡張できる構成を推奨します。

---

## ルート直下

- `README.md`
  - リポジトリ概要、最終目標、MVP、クイックスタート

- `.env` / `.env.example`
  - VTS接続先・サーバ設定などを記述（秘密情報は書かない）

- `.secrets/`
  - 認証トークンなどの秘密情報（Git管理しない）
  - 例: `.secrets/vts_token.json`

- `docs/`
  - 仕様書・設計メモ・運用ルール

---

## app/（FastAPI Backend）

- `app/main.py`
  - FastAPIエントリーポイント
  - 起動時に `VTSController` を初期化して、必要なら常駐接続する

- `app/vts/controller.py`
  - **VTSController本体**
  - 責務:
    - VTS WebSocketへの接続
    - 認証（トークン取得/保存/再利用）
    - ホットキー発火（MVP）
    - （拡張）パラメータ注入（口パク、揺れ、目線など）
    - 再接続（指数バックオフ）

- `app/vts/mapping.py`
  - `actionId -> hotkeyName` の対応表
  - 例:
    - `wave -> HK_WAVE`
    - `happy -> HK_HAPPY`

- `app/routes/vts_debug.py`
  - デバッグ用HTTP API
  - 例:
    - `POST /v1/vts/hotkey` : ホットキー発火
    - `GET /v1/vts/status` : 接続/認証状態確認

- `app/routes/ws.py`（必要なら）
  - Frontendと接続するWebSocket
  - `action`イベント受信→ `VTSController`へ委譲（実動作）

---

## scripts/（単体スモークテスト）

- `scripts/probe_hotkey.py`
  - **最初に動作確認するためのCLI**
  - FastAPIを介さずに
    - VTSに接続
    - 認証
    - 指定ホットキー発火
  を行う

---

## 設定（.env 例）

- `VTS_HOST=localhost`
- `VTS_PORT=8001`
- `VTS_PLUGIN_NAME=<あなたのプラグイン名>`
- `VTS_PLUGIN_DEVELOPER=<あなたの開発者名>`
- `VTS_TOKEN_PATH=.secrets/vts_token.json`

> 注意: VTSのAPIポートは環境により変更される可能性があるため、ユーザーが設定画面で確認できる導線を用意してください。

---

## 運用ルール（最低限）

- `.secrets/` は必ずgitignoreする
- 失敗時に例外を握り潰さず、`status` APIで最終エラーを返せるようにする
- VTSが落ちても自動復帰できるよう、再接続（指数バックオフ）を入れる
