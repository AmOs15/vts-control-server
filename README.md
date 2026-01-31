# vts-controller-fastapi

このリポジトリは、**VTube Studio（VTS）をPythonから制御**するための「検証〜本番移行可能な土台」を作るプロジェクトです。

- Backend（FastAPI）が司令塔となり、VTube StudioのAPI（WebSocket）へ接続して
  - ホットキーの発火（モーション・表情・アイテム表示など）
  - Live2Dパラメータの注入（口パク/揺れ/目線など）
  を実行します。

---

## 何がしたいか（最終目標）

**人の入力なしで AI により VTuberアバターが自動で動く状態**を作ることが最終目標です。

具体的には:

1. **待機モーション（体の揺れ/瞬き/うなずき等）**を自動挿入する（ランダム/状態遷移/ルール）
2. FastAPIのAPIアクセス時にアバターを動かす(Pythonで特定の動きを制御)

---

## MVP（最初に達成すること）

最短で価値が出るMVPは、次の3点です。

- PythonからVTSへ接続して認証できる
- VTS内で作成した **ホットキーをAPI経由で発火**できる
- Backend（FastAPI）のHTTP/WS経由で `action` を受け取り、VTSで動作が起きる

---

## 仕様・設計の方針

- VTS制御は **ホットキー駆動（離散アクション）** を基本にします（安定・デバッグしやすい）
- 連続制御（パラメータ注入）はMVP後に段階的に追加します（競合・優先順位のデバッグが増えるため）
- VTS接続・認証・再接続は `VTSController` に集約します
- トークンなどの秘密情報は `.secrets/` 配下に保存し、Gitにコミットしません

---

## クイックスタート（例）

> これは例です。実際の手順は `docs/structure.md` と `docs/vts-api-overview.md` を参照してください。

1. VTube Studioの設定で「プラグインAPIアクセスを許可」をONにする
2. VTSのAPIポート（通常 8001）を確認する
3. VTSでテスト用ホットキー（wave など）を作成する
4. Pythonのスモークテストでホットキーを発火してみる:
   - `python scripts/probe_hotkey.py --hotkey wave`
5. FastAPIを起動してHTTPから叩く:
   - `curl -X POST http://localhost:8080/v1/vts/hotkey -H 'Content-Type: application/json' -d '{"name":"wave"}'`
