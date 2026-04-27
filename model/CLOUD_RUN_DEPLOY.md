# Cloud Run デプロイ

`model/` は Cloud Run 上で `FastAPI` を動かす単一サービスとしてデプロイする。公開エンドポイントは `/`, `/health`, `/predict`, `/analyze-reward`。

## build and deploy

```bash
cd tea-pillar
bash scripts/deploy_ML/deploy_model_to_cloud_run.sh \
  --artifact-registry-repo YOUR_REPO \
  --model-image-tag v1 \
  --service-name nekkoflix-model \
  --allow-unauthenticated
```

## 環境変数

Cloud Run で Hugging Face の artifact を読む場合は以下を設定する。

```text
HF_MODEL_REPO_ID=your-org/nekkoflix-contextual-bandit
HF_MODEL_REVISION=main
HF_TOKEN=...
```

ローカル bundle を使う場合は次を設定する。

```text
MODEL_ARTIFACT_DIR=/app/artifacts
```

Cloud Run 起動後の `/predict` は、artifact bundle 内の `reward_regressor.joblib`
と `feature_columns.json` を読み、`candidate_video_ids` ごとの
`predicted_rewards` を返す。
