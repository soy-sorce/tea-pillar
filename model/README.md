# model

`docs/ja/MODELING.md` に準拠したモデル実装ディレクトリ。Cloud Run 上の FastAPI
サービスとして動かし、役割を次の 2 つに分ける。

- `/predict`: 静止画と任意音声からコンテキスト特徴量・補助ラベル・候補動画ごとの
  `predicted_rewards` を返す
- `/analyze-reward`: 反応動画から `paw_hit_count` と `gaze_duration_seconds` を算出し、
  `reward` を返す

Thompson Sampling 自体は backend が Firestore の `bandit_state` を使って実行する。
この `model/` では、動画ベース reward で学習した reward regressor を `/predict`
で利用する。

## Current status

- `/`, `/predict`, `/analyze-reward`, `/health` を持つ FastAPI app を提供する
- `reward_regressor.joblib`, `feature_columns.json`, `bandit_params.json`,
  `feature_schema.json`, `query_mapping.json`, `training_metadata.json`,
  `reward_formula.json` を artifact bundle として扱う
- `FeatureExtractor` は ML-analysis の `MultiModalFeatureExtractor` と同系統の実装を持つ
- `RewardRegressor` は `(before features, template_id) -> reward` を予測する
- artifact はローカルディレクトリまたは Hugging Face Hub から解決できる
- `/analyze-reward` は GCS 上の反応動画を読み、YOLOv8 と MediaPipe を用いた
  動画ベース reward 解析を行う

## Related docs

- `HUGGINGFACE_PUBLISHING.md`
- `CLOUD_RUN_DEPLOY.md`
