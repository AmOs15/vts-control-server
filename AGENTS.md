# Repository Guidelines

## Project Structure & Module Organization
- `README.md` と `docs/` に方針・背景を集約しています。設計意図は `docs/structure.md` を最初に確認してください。
- `app/` は FastAPI 実装の配置先（現状は骨組み）。VTS 接続ロジックはここに集約する方針です。
- `scripts/` は単体スモークテスト用の CLI 置き場です（例: `scripts/probe_hotkey.py`）。
- 設定は `.env` / `.env.example`、秘密情報は `.secrets/` に保存し、Git 管理外にします。
- 依存管理は `pyproject.toml` と `uv.lock` を基準にします。
- 詳細な設計メモや運用ルールは `docs/` に集約されています。

## Build, Test, and Development Commands
- 依存インストール: `uv sync`（uv を使用する場合）。
- スモークテスト例: `uv run python scripts/probe_hotkey.py --hotkey wave`。
- ルートの `main.py` は簡易プレースホルダーです。
- FastAPI を追加したら `uvicorn app.main:app --reload` を開発起動コマンドとして採用する想定です（実装後に更新）。

## Coding Style & Naming Conventions
- Python 3.10 以上、インデントはスペース 4。
- 命名: 関数/変数は `snake_case`、クラスは `PascalCase`、定数は `UPPER_SNAKE`。
- 型ヒントは可能な範囲で付与し、設定値は `pydantic-settings` でまとめる方針です。
- Lint/format は未導入のため、導入時は `pyproject.toml` に統一設定を追加してください。

## Testing Guidelines
- 現状テストフレームワークと `tests/` は未整備です。
- 追加する場合は `tests/` 配下に `test_*.py` で配置し、実行手順を README に追記してください。
- VTS 連携変更時は、接続・認証・ホットキー発火の手動確認手順を PR に記載してください。

## Commit & Pull Request Guidelines
- 既存の履歴は `種別: 内容` 形式（例: `add: docs`, `setup: uv`）。同形式で簡潔に。
- PR には目的、変更点、動作確認（コマンド/結果）を明記してください。
- `.env` の追加・変更、必要な VTS 設定（ポート/ホットキー名）も PR に記載します。

## Security & Configuration Tips
- `.secrets/` と `.env` は Git 管理外です。トークンは `.secrets/vts_token.json` に保存します。
- VTS 側の「プラグイン API アクセス許可」とポート設定を事前に確認してください。

## Documentation & References
- API 概要や認証フローは `docs/vts-api-overview.md` に整理されています。
- 仕様に関わる変更を入れた場合は、該当ドキュメントの更新も PR に含めてください。
- README のクイックスタート手順と実装が乖離しないように維持します。
