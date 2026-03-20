# model

`docs/ja/MODELING.md` と `docs/_internal/Phase0_Endpoint_Contract.md` に準拠した
Custom Endpoint 実装ディレクトリ。

現時点では、`model/artifacts/` に学習成果物一式を配置済みである。実行時の挙動は以下。

- 成果物が `model/artifacts/` にあればそれをロードする
- 画像特徴量は `tea-pillar-ML-analysis` と同じ `emotion / pose / clip` 抽出器で計算する
- `meow` は v1 では optional とし、未統合時は `null` を返す

通常運用では、実 extractor と artifact を使う想定である。

## Current status

- `/predict` と `/health` を持つ FastAPI app を提供する
- `feature_columns.json`, `video_id_mapping.json`, `clip_prompts.json`,
  `training_metadata.json` は v1 契約準拠の雛形を配置済み
- `reward_regressor.joblib` を含む artifact 一式を配置済み
- `Predictor` は artifact を読み込んで `predicted_rewards` を返せる
- `FeatureExtractor` は ML-analysis の `MultiModalFeatureExtractor` と同系統の実装を持つ
