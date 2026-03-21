# registry scripts

Artifact Registry へ初期 image を build / push するための補助スクリプト。

## backend

```bash
bash infra/ci/registry/push_backend_image.sh
```

任意 tag:

```bash
bash infra/ci/registry/push_backend_image.sh initial
```

## frontend

```bash
bash infra/ci/registry/push_frontend_image.sh
```

任意 tag:

```bash
bash infra/ci/registry/push_frontend_image.sh initial
```

いずれも以下を前提とする。

- `gcloud auth login` 済み
- `gcloud config set project gcp-hackathon-2026` 済み
- Artifact Registry repository `nekkoflix` が存在する
