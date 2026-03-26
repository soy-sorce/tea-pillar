# MODELING.md

## モデル設計書 v2
### 動画ベース報酬ラベルと reward prediction による猫向け動画選択モデル

| 項目 | 内容 |
|---|---|
| ドキュメント名 | MODELING.md |
| バージョン | v2.1 |
| 作成日 | 2026-03-27 |
| ステータス | Draft |
| 主目的 | 猫の事前状態から動画ごとの期待報酬を予測し、動画視聴後の反応動画から真の報酬を回収して継続改善するモデルを定義する |

---

## 目次

1. [この設計書の目的](#1-この設計書の目的)
2. [問題の再定義](#2-問題の再定義)
3. [結論サマリ](#3-結論サマリ)
4. [システム全体におけるモデルの役割](#4-システム全体におけるモデルの役割)
5. [採用モデル一覧](#5-採用モデル一覧)
6. [特徴量設計](#6-特徴量設計)
7. [報酬設計](#7-報酬設計)
8. [学習設計](#8-学習設計)
9. [推論設計](#9-推論設計)
10. [デプロイ設計](#10-デプロイ設計)
11. [入出力スキーマ](#11-入出力スキーマ)
12. [学習成果物](#12-学習成果物)
13. [開発・検証フロー](#13-開発検証フロー)
14. [v2 の制約と既知のズレ](#14-v2-の制約と既知のズレ)
15. [今後の拡張方針](#15-今後の拡張方針)

---

## 1. この設計書の目的

本ドキュメントは、猫向け動画選択モデルを以下の観点で定義する。

- 猫の「事前状態」と「視聴後行動」をどう分離して扱うか
- 反応動画からどのように真の報酬を作るか
- その報酬を教師にしてどのような reward predictor を学習するか
- なぜ online 更新として Contextual Bandit × Thompson Sampling を併用するか
- 学習済み成果物をどのような形で Hugging Face / Cloud Run に配置するか

---

## 2. 問題の再定義

### 2.1 なぜ通常のレコメンドではないか

一般的な動画レコメンドは「ユーザーが好むコンテンツを予測する」問題である。しかしこの定式化は Nekkoflix では成立しない。

猫は好きと言えない。評価もできない。履歴も少ない。

したがって、この問題を以下のように再定義する。

> **「猫の視聴前状態から、視聴後に最も大きな行動反応を引き起こす動画を予測する問題」**

ここで重要なのは、**教師信号は視聴後にしか得られない**ことである。

### 2.2 `before` と `after` の役割分担

本設計では、データを次の 2 つに分けて扱う。

| 区分 | 役割 |
|---|---|
| `before` 画像・音声 | 推論時に利用可能な入力特徴 |
| `after` / reaction 動画 | 学習時にのみ利用可能な報酬ラベル生成元 |

つまり、**本番推論では `before` しか使えない**。  
一方で、**学習時には `after` 動画から真の reward を作り、その reward を教師にして `before -> reward` の対応を学習する**。

### 2.3 なぜ動画ベース報酬が必要か

猫の「好み」を直接観測することはできない。しかし、猫が行動を起こした事実は観測できる。

猫パンチ（画面への接触）と注視時間を報酬としたのは、これが**猫の関与を示す観測可能な行動信号**だからである。

感情推定を報酬に使うと「本当に楽しんでいるのか」という解釈問題が残る。行動ベースに絞ることで、観測可能な事実のみを学習信号にできる。

### 2.4 なぜ reward predictor を持つのか

本番時には `after` 動画がまだ存在しないため、その場で真の reward は分からない。  
したがって、学習時に

```text
(before 特徴量, template_id) -> reward
```

を学習し、本番では各候補動画に対する **期待報酬 `predicted_rewards`** を返す必要がある。

### 2.5 なぜ Thompson Sampling も併用するのか

reward predictor があっても、猫ごとの個体差やデータ不足は残る。  
そのため、事前予測だけで全てを決めるのではなく、

- reward predictor = offline 事前知識
- Thompson Sampling = online 探索と適応

を組み合わせる。

---

## 3. 結論サマリ

v2.1 で採用するモデル方針は以下である。

1. `before` の猫画像・任意音声から Hugging Face 既存モデルで特徴量を抽出する
2. `after` / reaction 動画から YOLOv8 と MediaPipe で真の reward を計算する
3. 学習時は `(before 特徴量, template_id) -> reward` の reward predictor を学習する
4. 本番の `/predict` は `features`, `aux_labels`, `predicted_rewards` を返す
5. backend は `predicted_rewards` と `bandit_state` を使って template を選択する
6. 視聴後の反応動画から真の reward を回収し、backend が `bandit_state` を更新する

---

## 4. システム全体におけるモデルの役割

```text
猫の静止画・任意音声・候補クエリIDを backend から受領
         ↓
model service /predict
  - 感情分類
  - pose / clip 特徴抽出
  - optional meow 補助分類
  - reward predictor による候補動画ごとの predicted_rewards
         ↓
features + aux_labels + predicted_rewards
         ↓
Backend が state_key を構築
  - {meow_label or unknown}_{emotion_label}_{clip_top_label}
         ↓
Backend が predicted_rewards と Firestore の bandit_state を参照して選択
         ↓
Gemini でユーザーコンテキストを加えて拡張
         ↓
Veo3-fast で動画生成
         ↓
猫に再生（8s）
         ↓
再生中の反応動画を GCS に upload
         ↓
backend の BackgroundTasks が /analyze-reward を呼ぶ
         ↓
猫パンチ検出（YOLOv8）+ 注視時間（MediaPipe）
         ↓
真の reward 計算 → backend が bandit_state を更新
```

### 4.1 コンポーネントと配置

| コンポーネント | 役割 | 配置 |
|---|---|---|
| 感情分類モデル | 静止画から感情特徴を抽出 | Cloud Run（Hugging Face からロード） |
| pose / clip 抽出器 | 静止画から補助特徴を抽出 | Cloud Run |
| 鳴き声分類モデル | 音声から状態を補助的に抽出 | Cloud Run（optional） |
| reward predictor | `before` 特徴量と template_id から期待 reward を予測 | Cloud Run（独自学習 artifact） |
| 猫パンチ検出 | 動画クリップから猫パンチ数を推定 | Cloud Run（YOLOv8） |
| 注視時間計測 | 動画クリップから画面注視時間を推定 | Cloud Run（MediaPipe / fallback 近似） |
| Thompson Sampling | online 探索・適応 | Backend が Firestore `bandit_state` を参照して実行 |
| Gemini | クエリ拡張 | Backend から API 呼び出し |
| Veo3-fast | 動画生成 | Backend から API 呼び出し |

---

## 5. 採用モデル一覧

### 5.1 特徴抽出モデル

| 用途 | モデル ID | 備考 |
|---|---|---|
| 猫顔感情分類 | `semihdervis/cat-emotion-classifier` | 7 クラス分類 |
| pose 抽出 | `usyd-community/vitpose-plus-small` | 姿勢特徴圧縮に使用 |
| clip 補助特徴 | `openai/clip-vit-base-patch32` | 補助的な scene / interest 特徴 |
| 猫鳴き声分類 | `IsolaHGVIS/Cat-Meow-Classification` | optional |

### 5.2 報酬ラベル生成モデル

| 用途 | モデル / ライブラリ | 備考 |
|---|---|---|
| 猫パンチ検出 | `YOLOv8` | cat / paw 周辺動作の近似検出 |
| 注視時間計測 | `MediaPipe` | 顔向き推定。利用不可時は近似 fallback |

### 5.3 独自学習モデル

| 用途 | 内容 |
|---|---|
| reward predictor | `before` 特徴量と template_id から期待 reward を予測する回帰モデル |
| bandit bootstrap | Thompson Sampling 初期化に使う `alpha / beta` や query mapping |

---

## 6. 特徴量設計

### 6.1 `before` 画像から得る感情特徴量

`semihdervis/cat-emotion-classifier` の全 7 クラスの出力スコアをそのまま使う。

| 特徴量名 | 内容 |
|---|---|
| `emotion_happy` | happy スコア |
| `emotion_sad` | sad スコア |
| `emotion_angry` | angry スコア |
| `emotion_scared` | scared スコア |
| `emotion_surprised` | surprised スコア |
| `emotion_disgusted` | disgusted スコア |
| `emotion_neutral` | neutral スコア |

### 6.2 `before` 画像から得る補助特徴量

- pose 特徴
- clip ベース補助特徴
- `clip_top_label`

### 6.3 任意音声から得る補助ラベル

`IsolaHGVIS/Cat-Meow-Classification` の出力ラベルを `meow_label` として使う。  
音声がない場合は `null` を許容する。

### 6.4 reward predictor の最終入力

```text
before 特徴量 + optional meow + template_id
```

---

## 7. 報酬設計

### 7.1 入力

報酬の計算には**視聴後動画クリップ**が必要である。猫パンチも注視時間も静止画では取れない。

```text
reaction video（8s）
    ├── YOLOv8 による cat / paw 周辺動作解析
    └── MediaPipe による顔向き近似・注視時間解析
```

### 7.2 基本指標

| 指標 | 計測方法 | 活用モデル | 必要な入力 |
|---|---|---|---|
| `paw_hit_count` | 画面領域へ向かう高速接近イベント数 | YOLOv8 | 動画クリップ |
| `gaze_duration_seconds` | 画面方向を向いていた累積時間 | MediaPipe | 動画クリップ |

### 7.3 報酬の計算

```text
reward = α × paw_hit_count + β × gaze_duration_seconds
```

この reward が、reward predictor の教師ラベルになる。

### 7.4 学習時と本番時の違い

| フェーズ | 使用可能情報 |
|---|---|
| 学習時 | `before` 特徴量 + `after` 動画由来 reward |
| 本番時 | `before` 特徴量のみ |

したがって、本番では真の reward は直接使えず、学習済み reward predictor の `predicted_rewards` を使う。

---

## 8. 学習設計

### 8.1 学習サンプルの定義

1 サンプルは次の組で定義する。

```text
(before_image, optional before_audio, template_id, after_video) -> reward
```

### 8.2 学習フロー

1. `before` 画像・音声から特徴量を抽出する
2. `after` 動画から `paw_hit_count`, `gaze_duration_seconds`, `reward` を作る
3. `template_id` を特徴に加える
4. `reward` を教師として回帰モデルを学習する

### 8.3 学習対象

回帰モデルの入力と出力は次のとおり。

```text
入力: before 特徴量 + template_id
出力: expected reward
```

### 8.4 online 更新

本番では視聴後に真の reward を追加で回収し、backend が `bandit_state` を更新する。

つまり、

- offline: reward predictor を学習
- online: Thompson Sampling で探索・適応

の二段構えである。

---

## 9. 推論設計

### 9.1 推論フロー

1. frontend / backend が `before` 画像・任意音声・文脈を受け取る
2. backend が model service `/predict` を呼ぶ
3. `/predict` は `features`, `aux_labels`, `predicted_rewards` を返す
4. backend が `state_key` を構築する
5. backend が `predicted_rewards` と `bandit_state` を参照して template を選ぶ
6. backend が Gemini / Veo に渡す
7. 動画再生後、backend が `/analyze-reward` を呼び、真の reward を回収する
8. backend が `bandit_state` を更新する

### 9.2 推論アルゴリズム

```python
prediction = model_predict(before_image, optional_audio, candidate_video_ids)

features = prediction["features"]
aux_labels = prediction["aux_labels"]
predicted_rewards = prediction["predicted_rewards"]

state_key = build_state_key(aux_labels)
bandit_state = load_bandit_state(state_key)

selected_query = select_with_regression_plus_bandit(
    predicted_rewards=predicted_rewards,
    bandit_state=bandit_state,
)

# 視聴後
reward = analyze_reward(after_video)
update_bandit_state(state_key, selected_query, reward)
```

### 9.3 選択戦略

本番の選択は次のいずれかで運用する。

1. `predicted_rewards` の argmax
2. `predicted_rewards + Thompson Sampling bonus`
3. `predicted_rewards` を事前分布として Thompson Sampling に反映

ハッカソン期間中は 2 を第一候補とする。

---

## 10. デプロイ設計

### 10.1 デプロイ先

全モデルは **Cloud Run** 上に配置し、API として呼び出す。Vertex AI は使用しない。

### 10.2 Cloud Run の構成

| エンドポイント | 内容 |
|---|---|
| `/predict` | 画像・音声を受け取り、特徴量・補助ラベル・候補ごとの期待 reward を返す |
| `/analyze-reward` | 反応動画を受け取り、猫パンチ数・注視時間・真の報酬を返す |
| `/health` | ヘルスチェック |

### 10.3 モデルの配置方針

- Hugging Face 既存モデルは model Cloud Run 起動時または初回推論時にロードする
- 独自学習成果物は Hugging Face に公開する
- Thompson Sampling の実行主体は backend とする
- backend は Firestore の `bandit_state` を正本として参照・更新する

### 10.4 独自モデルの Hugging Face 公開

独自学習成果物と bandit bootstrap artifact を Hugging Face に公開する。

```text
huggingface.co/{org}/nekkoflix-contextual-bandit
```

---

## 11. 入出力スキーマ

### 11.1 `/predict` 入力

```json
{
  "image_base64": "<base64>",
  "audio_base64": "<base64 or null>",
  "candidate_video_ids": ["query-1", "query-2", "...", "query-10"]
}
```

### 11.2 `/predict` 出力

```json
{
  "features": {
    "emotion_happy": 0.18,
    "emotion_sad": 0.11,
    "emotion_angry": 0.05,
    "emotion_scared": 0.03,
    "emotion_surprised": 0.42,
    "emotion_disgusted": 0.02,
    "emotion_neutral": 0.19
  },
  "aux_labels": {
    "emotion_label": "surprised",
    "clip_top_label": "curious_cat",
    "meow_label": "waiting_for_food"
  },
  "predicted_rewards": {
    "query-1": 0.12,
    "query-2": 0.08,
    "query-4": 0.31
  }
}
```

### 11.3 `/analyze-reward` 入力

```json
{
  "reaction_video_gcs_uri": "gs://bucket/reaction.mp4",
  "session_id": "session-1",
  "template_id": "query-4",
  "state_key": "unknown_surprised_curious_cat"
}
```

### 11.4 `/analyze-reward` 出力

```json
{
  "paw_hit_count": 3,
  "gaze_duration_seconds": 5.2,
  "reward": 0.72
}
```

### 11.5 backend の選択入力

```json
{
  "features": { ... },
  "candidate_query_ids": ["query-1", "query-2", "...", "query-10"],
  "predicted_rewards": {
    "query-1": 0.12,
    "query-2": 0.08,
    "query-4": 0.31
  }
}
```

---

## 12. 学習成果物

| ファイル | 内容 |
|---|---|
| `reward_regressor.joblib` | `(before 特徴量, template_id) -> reward` を学習した回帰器 |
| `feature_columns.json` | 回帰器入力列の定義 |
| `query_mapping.json` | クエリ ID と動画生成テンプレートの対応 |
| `training_metadata.json` | 学習件数、使用モデル、reward 統計 |
| `reward_formula.json` | `paw_alpha`, `gaze_beta` など reward 設計 |
| `bandit_params.json` | Thompson Sampling 初期化用 alpha / beta |

---

## 13. 開発・検証フロー

### 13.1 学習フロー

1. 収集データから `before` / `after` の manifest を作る
2. `before` から context features を抽出する
3. `after` 動画から真の reward を抽出する
4. reward predictor を学習する
5. bandit bootstrap artifact を生成する
6. 成果物を Hugging Face に公開する

### 13.2 デプロイフロー

1. model service を Cloud Run にデプロイする
2. Cloud Run が Hugging Face artifact を取得する
3. backend から `/predict`, `/analyze-reward` を呼ぶ

### 13.3 検証項目

- 同一入力で再現性のある特徴量が返ること
- `after` 動画から `reward` が安定して算出されること
- reward predictor が `before` だけで有意な予測を返すこと
- backend で `predicted_rewards` を用いた選択が動作すること
- 視聴後 reward で `bandit_state` が更新されること

---

## 14. v2 の制約と既知のズレ

### 14.1 学習データ量の制約

現状は猫数・セッション数が少ない。reward predictor は過学習リスクが高い。

### 14.2 reward 抽出の近似性

YOLOv8 と MediaPipe による猫パンチ・注視時間は近似であり、真の行動理解ではない。

### 14.3 MediaPipe の互換差

環境によって `mediapipe` の API が異なる可能性があり、fallback 実装が必要になる。

### 14.4 online / offline 併用の複雑さ

`predicted_rewards` と `bandit_state` を併用するため、選択戦略の解釈とチューニングが必要になる。

---

## 15. 今後の拡張方針

- reward predictor を単純回帰器からより強いモデルへ更新する
- YOLOv8 / MediaPipe 部分を猫専用 fine-tuning モデルへ置き換える
- `before` 画像だけでなく短い pre-roll 動画も入力に使う
- Thompson Sampling と reward predictor の統合をベイズ的に整理する
