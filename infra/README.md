# infra

`infra/` は `tea-pillar` の GCP インフラ定義と補助スクリプトを置くディレクトリ。Terraform を中心に、API Gateway 定義、Cloud Build 定義、Firestore seed を管理する。

設計の背景は `../docs/ja/INFRASTRUCTURE.md` を参照。

## 構成

```text
infra/
├── apigateway/
│   └── openapi.yaml
├── ci/
│   ├── cloud_build/
│   │   ├── cloudbuild-apigateway.yaml
│   │   ├── cloudbuild-backend.yaml
│   │   ├── cloudbuild-frontend.yaml
│   │   └── cloudbuild-model.yaml
├── firestore_initial_setup/
│   ├── seed_firestore.py
│   └── templates.json
└── terraform/
    ├── environments/
    │   ├── dev/
    │   └── prod/
    └── modules/
        ├── api_gateway/
        ├── artifact_registry/
        ├── cloud_build_trigger/
        ├── cloud_run/
        ├── firestore/
        ├── gcs/
        ├── iam/
        ├── vertex_ai/
        └── vpc/
```

## 何を管理しているか

- Cloud Run
  - frontend
  - backend
  - model
- API Gateway
- Firestore
- GCS bucket
- Artifact Registry
- Cloud Build trigger
- IAM
- Vertex AI 関連 resource
- VPC

## Terraform

環境ごとに `infra/terraform/environments/{dev,prod}` を使う。module は `infra/terraform/modules` に分離している。

基本手順の例:

```bash
cd infra/terraform/environments/dev
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan
terraform apply
```

prod でも同様に `infra/terraform/environments/prod` で実行する。

## tfvars で主に入れる値

- `project_id`
- `region`
- service 名
- image 名
- bucket 名
- Firestore / API Gateway / IAM に必要な naming

まず `terraform.tfvars.example` を見て埋める。

## API Gateway

- 定義ファイル: `infra/apigateway/openapi.yaml`
- backend の公開 endpoint と CORS 前提はここに影響する

backend 側の route を変更したら、API Gateway 側の path / method / backend address の整合も確認する。

## Cloud Build

`infra/ci/cloud_build/` に各サービス向けの build 定義がある。

- `cloudbuild-frontend.yaml`
- `cloudbuild-backend.yaml`
- `cloudbuild-model.yaml`
- `cloudbuild-apigateway.yaml`

Terraform の trigger module と組み合わせて使う前提。

## Firestore 初期化

`infra/firestore_initial_setup/templates.json` は template collection の seed データ。

投入例:

```bash
cd infra/firestore_initial_setup
python seed_firestore.py
```

実行前に GCP credential と対象 project を確認すること。

## 運用時の注意

- `terraform.tfstate` や `.terraform/` は生成物。運用では remote state 利用を前提に整理した方がよい
- `templates.json` を変更したら backend の local fallback template と差分が出ていないか確認する
- backend / frontend / model の Cloud Run 設定変更時は Terraform, Cloud Build, 実装 README の 3 点がずれやすい
- API Gateway と backend route の不整合はローカルでは見えず、本番で初めて出るので必ず差分確認する

## この README の守備範囲

- インフラ資産がどこにあるか
- どのファイルをどう更新すべきか
- Terraform / Cloud Build / Firestore seed の入口

プロダクト仕様やアプリの動作フロー自体は `docs/` を参照する。
