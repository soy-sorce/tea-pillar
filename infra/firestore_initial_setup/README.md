# Firestore Initial Setup

このディレクトリは、Firestore の初期データ投入を Terraform と分離して管理するための領域である。

現時点では以下を含む。

- `templates.json`
  - `templates` コレクションへ投入する初期テンプレート定義
- `seed_firestore.py`
  - 初期データ投入スクリプト

## 前提

- Firestore database が作成済みであること
- 実行環境で ADC が有効であること
- `google-cloud-firestore` が利用可能であること

## 実行例

```bash
python infra/firestore_initial_setup/seed_firestore.py \
  --project-id gcp-hackathon-2026 \
  --database-id "(default)" \
  --seed-bandit-table
```

`--dry-run` を付けると、Firestore には書き込まず投入内容だけを表示する。

```bash
python infra/firestore_initial_setup/seed_firestore.py \
  --project-id gcp-hackathon-2026 \
  --dry-run
```

## データソース

`templates.json` は以下の train-data から整理した。

- `/home/shouh/team_project/GCP_hackathon_2026/tea-pillar-ML-analysis/script/v1/prepare-videos/output/train-data`

各 `video-N/video_data.csv` の以下列を主に参照している。

- `内容`
- `生成クエリ`
- `Gen Query`
- `カテゴリ`

## 方針

- `template_id` は `video-1` から `video-10`
- `prompt_text` は Gemini へ渡す seed として `Gen Query` を採用
- 管理用メタデータとして日本語説明やカテゴリも保存する
- `bandit_table` はオプションで初期化できる

## bandit_table の扱い

Backend は `bandit_table` が空でも選択自体は可能だが、初期コールドスタート時の見通しをよくするため、以下の状態キーで初期化できるようにする。

- `unknown_{emotion_label}_{clip_top_label}`

`emotion_label` は以下。

- `happy`
- `sad`
- `angry`

`clip_top_label` は以下。

- `attentive_cat`
- `relaxed_cat`
- `stressed_cat`
- `playful_cat`
- `sleepy_cat`
- `curious_cat`
- `alert_cat`
- `comfortable_cat`
