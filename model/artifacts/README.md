# artifacts

このディレクトリには以下の成果物を配置する。

- `reward_regressor.joblib`
- `feature_columns.json`
- `bandit_params.json`
- `feature_schema.json`
- `query_mapping.json`
- `training_metadata.json`
- `reward_formula.json`

predictor は runtime で Hugging Face 特徴抽出器を使うため、artifact は主に
reward analyzer と backend bootstrap 用のメタデータとして扱う。
