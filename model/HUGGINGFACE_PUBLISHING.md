# Hugging Face 公開手順

この `model/` ディレクトリは、Cloud Run 上の FastAPI サービスが読み込む
MODELING.md v2 artifact bundle を Hugging Face Hub に置けるようにしてある。

## 前提

- `HF_TOKEN` を発行済み
- artifact bundle が `model/artifacts/` に生成済み
- 必須ファイル:
  - `reward_regressor.joblib`
  - `feature_columns.json`
  - `bandit_params.json`
  - `feature_schema.json`
  - `query_mapping.json`
  - `training_metadata.json`
  - `reward_formula.json`

## 1. artifact を再生成

```bash
cd tea-pillar/model
uv run python scripts/build_modeling_v2_artifacts.py \
  --input ./train-data-20260326T165440Z-3-001.zip
```

## 2. Hub にアップロード

```bash
export HF_TOKEN=...
cd model
uv run python scripts/publish_artifacts_to_huggingface.py \
  --repo-id your-org/nekkoflix-contextual-bandit
```

非公開で始めるなら `--private` を付ける。

## 3. Cloud Run で使う

Cloud Run 側には次の環境変数を渡す。

```text
HF_MODEL_REPO_ID=your-org/nekkoflix-contextual-bandit
HF_MODEL_REVISION=main
HF_TOKEN=...
```

`HF_MODEL_CACHE_DIR` を指定すると snapshot の保存先を固定できる。ローカル artifact を直接使う場合は `MODEL_ARTIFACT_DIR` を指定する。
