# Firestore Initial Setup

このディレクトリは、Firestore の初期データ投入を Terraform と分離して管理するための領域である。

現時点では以下を含む。

- `templates.json`
  - `templates` コレクションへ投入する初期テンプレート定義
- `seed_firestore.py`
  - `templates` と `bandit_state` を初期投入するスクリプト

## 前提

- Firestore database が作成済みであること
- 実行環境で ADC が有効であること
- `google-cloud-firestore` が利用可能であること

## 実行例

```bash
python infra/firestore_initial_setup/seed_firestore.py \
  --project-id gcp-hackathon-2026 \
  --database-id "(default)" \
  --seed-bandit-state
```

`--dry-run` を付けると、Firestore には書き込まず投入内容だけを表示する。

```bash
python infra/firestore_initial_setup/seed_firestore.py \
  --project-id gcp-hackathon-2026 \
  --dry-run
```

## 方針

- `template_id` は `video-1` から `video-10`
- `prompt_text` は Gemini へ渡す seed として `Gen Query` を採用
- `bandit_state` は Thompson Sampling 用に初期化する
- 初期値は `alpha=1`, `beta=1`, `selection_count=0`, `reward_sum=0.0`

## bandit_state の扱い

初期化対象の state key は、現 backend / docs の離散 state key 形式に合わせる。

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

## 今後の拡張

将来的に `MODELING.md` の連続コンテキスト表現へ完全移行する場合、`bandit_state` の key 設計は再検討する。
