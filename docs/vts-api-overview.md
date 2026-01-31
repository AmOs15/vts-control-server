# VTube Studio API 概要（VTS Plugin API）

## 1. 全体像

VTube Studioには「公開API」があり、外部アプリ/プラグインから **WebSocket(JSON)** で制御できます。

できること（代表例）:
- ホットキー発火（モーション/表情/アイテム/シーン切替など）
- 顔トラッキング/Live2Dパラメータ値の入力（外部データ注入）
- モデルやアイテムの読み込み/操作
- 各種イベント通知（イベント購読）

---

## 2. 接続方式

- 接続先: `ws://localhost:8001`（デフォルト）
- メッセージ: JSON（テキストフレーム）
- ユーザー設定によりポート変更が可能

### 接続前提
- VTube Studioの設定で「プラグインAPIアクセスを許可」をONにする必要があります
- 企業ネットワーク等ではFW/セキュリティソフトがローカルWSを塞ぐ場合があります

---

## 3. 認証フロー（ざっくり）

VTS APIは「トークン発行 → トークンで認証」という流れです。

1) Token Request
- `AuthenticationTokenRequest` を送り、トークン発行を要求する
- VTS側で「このプラグインを許可しますか？」のダイアログが出る
- 許可されるとトークンが返る

2) Authentication
- 取得したトークンを使って `AuthenticationRequest` を送り、セッションを認証する
- 成功すると「このセッションで操作可能」になる

※トークンはローカルに保存して再利用できる（次回以降、許可ダイアログを省略できる）

---

## 4. 実装方針（このリポジトリの選択）

このリポジトリでは、最短で確実に動かすため **ホットキー発火**をMVPにします。

- VTS側でホットキーを作成する
- Pythonから「ホットキー一覧取得 → 指定ホットキー発火」を行う
- AI側の `actionId` を `hotkeyName` にマッピングして発火する

---

## 5. Pythonからの実装（推奨: pyvts）

Pythonで生のWebSocket実装も可能ですが、認証やメッセージ形式のミスを減らすため、
本プロジェクトでは `pyvts` の利用を推奨します。

pyvtsでできること（代表）:
- VTSへ接続
- トークン要求（ローカル保存）
- 認証
- 各種APIリクエスト送信

---

## 6. 最低限のJSONメッセージ例（イメージ）

※実際のフィールドはAPI仕様に合わせて実装してください。

### API状態確認（例）
{
  "apiName": "VTubeStudioPublicAPI",
  "apiVersion": "1.0",
  "requestID": "req-001",
  "messageType": "APIStateRequest"
}

### 認証トークン要求（例）
{
  "apiName": "VTubeStudioPublicAPI",
  "apiVersion": "1.0",
  "requestID": "req-002",
  "messageType": "AuthenticationTokenRequest",
  "data": {
    "pluginName": "MyPlugin",
    "pluginDeveloper": "MyName"
  }
}

### 認証（例）
{
  "apiName": "VTubeStudioPublicAPI",
  "apiVersion": "1.0",
  "requestID": "req-003",
  "messageType": "AuthenticationRequest",
  "data": {
    "pluginName": "MyPlugin",
    "pluginDeveloper": "MyName",
    "authenticationToken": "<TOKEN>"
  }
}

---

## 7. 注意点（macOS）

- macOSでは「VTSが非フォーカスでもホットキーを反応させたい」ケースで
  アクセシビリティ権限が必要になる場合があります。
- ただしAPI経由でホットキー発火する運用なら、影響は限定的です（環境差は要検証）

---

## 8. 参考リンク

- VTube Studio API Development (公式GitHub)
  https://github.com/DenchiSoft/VTubeStudio

- Plugins (VTS Wiki)
  https://github.com/DenchiSoft/VTubeStudio/wiki/Plugins

- pyvts (Pythonライブラリ)
  https://genteki.github.io/pyvts/
  https://github.com/Genteki/pyvts

- VTS APIの日本語メモ（接続/8001/許可などの要点）
  https://note.com/mega_gorilla/n/n927a17a40d36
