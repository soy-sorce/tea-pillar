# tea-pillar

猫の表情や鳴き声、ユーザーの文脈から猫向けの動画体験を生成し、その後の reaction まで含めて reward を学習に戻すマルチサービス構成のプロダクト。

プロダクトの要件、設計、モデリング方針は `docs/` を参照する。

- 日本語: `docs/README.md`, `docs/ja/`
- 英語: `docs/READMEen.md`, `docs/en/`

この README では、実装をローカルで開発するためのセットアップ手順だけを扱う。

## リポジトリ構成

```text
tea-pillar/
├── frontend/   # React + Vite
├── backend/    # FastAPI orchestration API
├── model/      # FastAPI model service
├── infra/      # Terraform / Cloud Build / API Gateway / Firestore seed
└── docs/       # 要件定義・設計書
```

## 前提ツール

必要なもの:

- `git`
- `docker` と `docker compose`
- Node.js `22`
- npm
- Python `3.11`
- `uv`

### uv の導入

未導入なら公式手順で入れる。

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

導入後の確認:

```bash
uv --version
python3 --version
node --version
npm --version
docker --version
docker compose version
```

## 最短セットアップ

3 サービスを同時起動する最短手順。

```bash
cp .env.compose.example .env.compose
cp backend/.env.example backend/.env
docker compose --env-file .env.compose up --build
```

起動先:

- frontend: `http://localhost:3000`
- backend: `http://localhost:8080`
- model: `http://localhost:8081`

補足:

- frontend から backend へは `http://localhost:8080`
- backend から model へは compose network 内で `http://model:8080`
- backend は `backend/.env` も読む
- GCP を使う endpoint を実際に叩くなら、追加の認証情報と resource 設定が必要

停止:

```bash
docker compose down
```

完全に build cache / volume も消す場合:

```bash
docker compose down -v
```

## 手動セットアップ

compose を使わず、各サービスを個別に起動したいときの手順。

### 1. frontend

```bash
cd frontend
npm ci
npm run dev -- --host 0.0.0.0 --port 3000
```

frontend の主な技術:

- React `19`
- Vite `8`
- TypeScript

backend API の接続先は `frontend/.env` で指定できる。ローカル開発では次が基本。

```bash
cd frontend
cp .env.example .env
```

`frontend/.env`:

```dotenv
VITE_BACKEND_URL=http://localhost:8080
```

### 2. backend

```bash
cd backend
cp .env.example .env
uv sync --extra dev
uv run uvicorn src.app:app --reload --host 0.0.0.0 --port 8080
```

backend の主な技術:

- FastAPI
- Pydantic Settings
- Firestore client
- Gemini / Veo / model service client

backend は `backend/.env` と実行時環境変数を読む。よく使うもの:

- `MODEL_SERVICE_URL`
- `FRONTEND_ORIGIN`
- `GCP_PROJECT_ID`
- `GCP_REGION`
- `GCS_BUCKET_NAME`
- `REACTION_VIDEO_BUCKET_NAME`
- `FIRESTORE_DATABASE_ID`

ローカルで model を同時起動しているなら:

```dotenv
MODEL_SERVICE_URL=http://localhost:8081
FRONTEND_ORIGIN=http://localhost:3000
```

### 3. model

```bash
cd model
uv sync --extra dev
uv run uvicorn src.app:app --reload --host 0.0.0.0 --port 8081
```

model の主な技術:

- FastAPI
- scikit-learn / LightGBM
- Hugging Face artifact loader
- MediaPipe / YOLOv8

artifact をローカル bundle から読む場合:

```bash
export MODEL_ARTIFACT_DIR=/home/shouh/team_project/GCP_hackathon_2026/tea-pillar/model/artifacts
```

Hugging Face から取得する場合:

```bash
export HF_MODEL_REPO_ID=your-org/your-model-repo
export HF_MODEL_REVISION=main
export HF_TOKEN=...
```

## GCP を使う開発

`generate` と reaction 解析の完全フローは、ローカル起動でも GCP 側 resource と認証が必要になる。

主に必要なもの:

- Firestore
- GCS bucket
- Gemini
- Veo
- 必要に応じて service account credential

代表的な env:

```dotenv
GCP_PROJECT_ID=...
GCP_REGION=asia-northeast1
GCS_BUCKET_NAME=...
REACTION_VIDEO_BUCKET_NAME=...
FIRESTORE_DATABASE_ID=(default)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
GCS_SIGNING_SERVICE_ACCOUNT_FILE=/path/to/credentials.json
```

compose を使う場合も、`.env.compose` と `backend/.env` の両方で管理できる。

## 静的解析とテスト

### frontend

```bash
cd frontend
npm run lint
npm run build
```

### backend

```bash
cd backend
uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy src
uv run pytest
```

### model

```bash
cd model
uv run ruff check src tests
uv run mypy src
uv run pytest
```

## 開発フローのおすすめ

初回:

1. `cp .env.compose.example .env.compose`
2. `cp backend/.env.example backend/.env`
3. `docker compose --env-file .env.compose up --build`

日常開発:

1. frontend の UI 修正は compose のまま `http://localhost:3000` で確認
2. backend / model は bind mount + `--reload` で自動反映
3. 変更前後で対象サービスの lint / test を個別に実行

commit 前:

1. frontend: `npm run lint && npm run build`
2. backend: `uv run ruff check src tests && uv run ruff format --check src tests && uv run mypy src && uv run pytest`
3. model: `uv run ruff check src tests && uv run mypy src && uv run pytest`

## 関連 README

- `frontend/README.md`
- `backend/README.md`
- `model/README.md`
- `infra/README.md`
