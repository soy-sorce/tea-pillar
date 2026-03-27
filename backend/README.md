# backend

`backend/` は `tea-pillar` の API サービス。`frontend` からの生成要求と reaction 動画登録を受け、`model` と外部 GCP サービスをオーケストレーションする。

設計・仕様の正本は `docs/` にある。特に以下を先に読むと全体像を追いやすい。

- `../docs/ja/Backend_Design.md`
- `../docs/ja/High_Level_Design.md`
- `../docs/ja/MODELING.md`
- `../docs/ja/INFRASTRUCTURE.md`

## 責務

- `POST /generate`
  - セッション作成
  - `model` の `/predict` 呼び出し
  - state key 構築
  - Thompson Sampling による template 選択
  - Gemini による prompt/query 生成
  - Veo 呼び出し
  - signed URL 発行
- `POST /sessions/{session_id}/reaction-upload-url`
  - reaction 動画アップロード用 signed URL 発行
- `POST /sessions/{session_id}/reaction`
  - reaction 動画の登録完了
  - reward 解析ジョブの起動

## ディレクトリ構成

```text
backend/
├── src/
│   ├── app.py                    # FastAPI entrypoint
│   ├── config.py                 # Settings
│   ├── dependencies.py           # FastAPI dependency provider
│   ├── clients/                  # 外部 API / 外部サービス client
│   ├── repositories/             # Firestore / ローカル data access
│   ├── domain/                   # enum などの domain model
│   ├── models/                   # request / response / internal model
│   ├── routers/                  # FastAPI route
│   └── services/                 # 業務ロジック
├── tests/
├── .env.example
├── Dockerfile
└── pyproject.toml
```

## 前提

- Python `3.11`
- `uv`
- GCP 連携を実際に使う場合は認証情報と各種 resource ID

`uv` 未導入なら公式手順で入れる。

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## セットアップ

```bash
cd backend
cp .env.example .env
uv sync --extra dev
```

最低限、ローカル開発でよく使う env は次。

- `MODEL_SERVICE_URL`
- `FRONTEND_ORIGIN`
- `GCP_PROJECT_ID`
- `GCS_BUCKET_NAME`
- `REACTION_VIDEO_BUCKET_NAME`
- `FIRESTORE_DATABASE_ID`

`config.py` の default で十分なものは `.env` に置かなくてよい。運用時に変える可能性がある connection / credential / resource 系を優先して定義する。

## ローカル起動

### 単体起動

```bash
cd backend
uv run uvicorn src.app:app --reload --host 0.0.0.0 --port 8080
```

### docker compose 経由

repo root で実行する。

```bash
cp .env.compose.example .env.compose
cp backend/.env.example backend/.env
docker compose --env-file .env.compose up --build backend model frontend
```

compose では次のポートを使う。

- backend: `http://localhost:8080`
- model: `http://localhost:8081`
- frontend: `http://localhost:3000`

backend から model へは compose network 内で `http://model:8080` に接続する。

## テストと静的解析

```bash
cd backend
uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy src
uv run pytest
```

スコープ別に回す場合:

```bash
cd backend
uv run pytest tests/unit
uv run pytest tests/integration
uv run pytest -k orchestrator
```

## 実装上の補足

- `clients/`
  - `GeminiClient`, `VeoClient`, `CatModelClient`, `SignedUrlGenerator`
- `repositories/`
  - `FirestoreClient`, `LocalTemplateRepository`
- `services/`
  - `GenerateOrchestrator`, `RewardAnalysisService`, `SessionPolicy`
- model service failure 時は local template fallback を使って生成フローを継続する
- Firestore template 取得失敗時も `src/data/templates.json` に fallback する

## 変更時の確認ポイント

- `config.py` に集約すべき runtime parameter が散っていないか
- route 層に業務ロジックが漏れていないか
- 外部境界の response validation が十分か
- `experience` / `production` の session policy を壊していないか
- Firestore failure 時に session status が不整合にならないか

## よくある作業

依存更新:

```bash
cd backend
uv sync --extra dev
```

lock 更新を伴う追加:

```bash
cd backend
uv add <package>
uv add --dev <package>
```

pre-commit を使う場合:

```bash
cd backend
uv run pre-commit install
```
