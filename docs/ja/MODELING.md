# MODELING.md

## モデル設計書 v1
### Cats Feature Extraction + Reward Regression for Template Selection

| 項目 | 内容 |
|---|---|
| ドキュメント名 | MODELING.md |
| バージョン | v2.0 |
| 作成日 | 2026-03-20 |
| ステータス | Draft |
| 対応設計 | `docs/ja/High_Level_Design.md`, `docs/ja/INFRASTRUCTURE.md` |
| 主目的 | 猫画像・音声から動画候補ごとの予測報酬を算出するモデルを定義し、Vertex AI Endpoint へデプロイ可能な形で整理する |

---

## 目次

1. [この設計書の目的](#1-この設計書の目的)
2. [結論サマリ](#2-結論サマリ)
3. [採用方針](#3-採用方針)
4. [システム全体におけるモデルの役割](#4-システム全体におけるモデルの役割)
5. [採用モデル一覧](#5-採用モデル一覧)
6. [モデル理論](#6-モデル理論)
7. [学習データ設計](#7-学習データ設計)
8. [特徴量設計](#8-特徴量設計)
9. [CLIP 類似度特徴の意味と扱い](#9-clip-類似度特徴の意味と扱い)
10. [報酬設計](#10-報酬設計)
11. [学習設計](#11-学習設計)
12. [推論設計](#12-推論設計)
13. [デプロイ設計](#13-デプロイ設計)
14. [入出力スキーマ](#14-入出力スキーマ)
15. [学習成果物](#15-学習成果物)
16. [実装責務の分割](#16-実装責務の分割)
17. [開発・検証フロー](#17-開発検証フロー)
18. [v1 の制約と既知のズレ](#18-v1-の制約と既知のズレ)
19. [今後の拡張方針](#19-今後の拡張方針)

---

## 1. この設計書の目的

本ドキュメントの目的は、猫向け動画選択に用いるモデルを以下の観点で一貫して定義することである。

- 学習時に何を入力し、何を予測するか
- 猫画像・音声からどのような特徴量を作るか
- Hugging Face 系モデルをどのように中間特徴抽出器として使うか
- 学習済みモデルをどのような形式で保存し、どこへデプロイするか
- Backend / Vertex AI Endpoint / Bandit の責務をどう分離するか

本設計書は、実験用 notebook の説明ではなく、**最終的に Vertex AI Endpoint へデプロイ可能な v1 モデル仕様書**として扱う。

---

## 2. 結論サマリ

v1 で採用するモデル方針は以下である。

1. 猫の状態理解には Hugging Face 系の既存モデルを継続利用する
2. それらの出力を中間特徴量ベクトルへ変換する
3. 最終意思決定モデルとしては `LightGBM Regressor` を採用する
4. Regressor は「猫状態特徴量 × 動画候補特徴量」から **予測報酬** を返す
5. Vertex AI Endpoint は動画候補ごとの予測報酬配列を返す
6. Backend はその配列に UCB を加算して最終テンプレートを選択する

重要な設計判断は以下である。

- v1 では `LightGBM Ranker` を本番採用しない
- v1 では動画特徴量は `video_id` の one-hot を採用する
- v1 では ViTPose の意味特徴量は厳密な部位工学ではなく、安定して計算できる幾何圧縮特徴を使う
- v1 では CLIP は「自然言語との類似度を返す意味特徴抽出器」として使う
- v1 では LightGBM は Vertex AI Endpoint 側に統合し、Backend 側では UCB のみ行う

現時点の正式実装前提は以下である。

- Vertex AI Custom Endpoint は 1 コンテナで `emotion / pose / clip / Reward Regressor` を実行する
- `meow` は optional とし、v1 では未入力時に `null` を許容する
- Endpoint は `features`, `aux_labels`, `predicted_rewards` を返す
- `features` の 23 次元キーは学習時と推論時で完全一致させる
- `backend` は特徴量抽出を行わず、`predicted_rewards` に UCB を加算する

---

## 3. 採用方針

### 3.1 なぜこの構成にするか

今回のプロダクトでは、学習データがまだ小さい。

- 猫数が少ない
- 1 猫あたりのセッション数が少ない
- 動画候補数に対してサンプル数が不足している

この条件では、複雑な強化学習や大規模 end-to-end 学習を本番用 v1 として採用するのはリスクが高い。

一方で、以下は既に現実的である。

- 既存の Hugging Face モデルで猫画像から安定した中間特徴を作る
- その中間特徴に対して木系モデルで小規模学習する
- 動画候補ごとのスコアを返す
- Bandit の exploration は Backend 側で行う

これにより、

- 学習パイプラインが単純になる
- 推論ロジックが説明可能になる
- モデルのデバッグが容易になる
- Vertex AI へのデプロイ構成が明快になる

### 3.2 採用しないもの

v1 では以下は本番採用しない。

- REINFORCE などの方策勾配法
- `LightGBM Ranker` 単独の本番採用
- 動画クエリ埋め込み + PCA を必須とする構成
- ViTPose キーポイントからの高度な解剖学的特徴量設計

これらは v2 以降の改善候補とする。

---

## 4. システム全体におけるモデルの役割

モデル層の責務は「猫の現在状態を数値化し、各動画候補に対する予測報酬を返すこと」である。

### 4.1 モデルの出力

モデルが返すのは、最終テンプレート ID ではなく以下である。

- 猫状態特徴量
- 状態キー生成に使う補助ラベル
- 各動画候補に対する `predicted_reward`

### 4.2 最終選択はどこで行うか

最終選択は Backend で行う。

```
predicted_reward(video_i)
  + UCB_bonus(video_i)
  = final_score(video_i)
```

これにより、モデルは exploitation、Backend は exploration を担当する。

### 4.3 配置

| コンポーネント | 役割 | 配置 |
|---|---|---|
| 猫特徴抽出モデル | 画像/音声から中間特徴量を作る | Vertex AI Endpoint |
| Reward Regressor | 候補動画ごとの予測報酬を返す | Vertex AI Endpoint |
| UCB Bandit | 探索ボーナスを加算する | Backend |
| Gemini | テンプレートから動画プロンプト再構築 | Backend から Vertex AI API 呼び出し |
| Veo | 動画生成 | Backend から Vertex AI API 呼び出し |

---

## 5. 採用モデル一覧

### 5.1 採用する Hugging Face / 既存モデル

| 用途 | モデル ID | 採用理由 | 備考 |
|---|---|---|---|
| 猫顔感情分類 | `semihdervis/cat-emotion-classifier` | 既存データ作成と整合しやすい | 実際の元ラベルは 7 クラス。v1 では `happy/sad/angry` を利用 |
| 猫ポーズ推定 | `usyd-community/vitpose-plus-small` | 実際に読み込み可能な公開モデル | docs の旧記述 `plus-plus-small` は v1 実装では使わない |
| ゼロショット意味特徴 | `openai/clip-vit-base-patch32` | 画像と自然言語の意味類似を数値化できる | 猫状態の補助特徴として利用 |
| 猫鳴き声分類 | `IsolaHGVIS/Cat-Meow-Classification` | 音声入力がある場合の状態把握 | v1 では optional。`emotion / pose / clip` を優先して統合する |

### 5.2 最終予測モデル

| 用途 | モデル | 採用理由 |
|---|---|---|
| 予測報酬算出 | `LightGBM Regressor` | 小規模データに強く、学習・保存・推論が軽量で、説明可能性が高い |

---

## 6. モデル理論

### 6.1 何を学習するか

v1 モデルが学習するのは以下の関数である。

```
f(cat_state_features, video_candidate_features) -> predicted_reward
```

ここで、

- `cat_state_features` は猫の before 状態を表すベクトル
- `video_candidate_features` は動画候補を表すベクトル
- `predicted_reward` はその動画を見せたときに期待される状態改善量

### 6.2 なぜ分類ではなく回帰か

分類にすると「どの動画が最良だったか」しか使えない。
しかし今回のデータには、動画ごとの反応の強弱がある。

例:

- video-4: +0.66
- video-5: +0.52
- video-8: +0.23
- video-10: -0.58

これらを 1 位/それ以外 に潰すと情報を失う。
そのため、v1 は reward の連続値をそのまま学習する回帰を採用する。

### 6.3 なぜ Ranker ではなく Regressor か

Ranker は理論的には魅力的だが、v1 時点では以下の理由で本番採用しない。

- 現データ量では group 構成が弱い
- relevance ラベル設計がまだ固まり切っていない
- 動作検証時に train fit の影響を受けやすい
- Backend 側に UCB があるため、Endpoint 側ではまず安定した報酬スコアを返す方がよい

したがって、v1 は **Reward Regressor + Backend UCB** を正規構成とする。

---

## 7. 学習データ設計

### 7.1 基本単位

学習データの 1 行は以下である。

```
1 猫 × 1 動画候補 × 1 セッション
```

### 7.2 セッション定義

1 セッションとは次を指す。

1. before 画像を取得
2. ある動画候補を見せる
3. after 画像を取得
4. before / after の差から reward を計算

### 7.3 v1 の教師データ構造

```json
{
  "session_id": "kurochan_video-4",
  "cat_id": "kurochan",
  "video_id": "video-4",
  "before": {
    "emotion_happy": 0.12,
    "emotion_sad": 0.21,
    "emotion_angry": 0.05,
    "pose_area_ratio": 0.33,
    "clip_attentive_cat": 0.27
  },
  "after": {
    "emotion_happy": 0.38,
    "emotion_sad": 0.08,
    "emotion_angry": 0.03,
    "pose_area_ratio": 0.41,
    "clip_attentive_cat": 0.44
  },
  "reward": 0.66
}
```

### 7.4 学習データソース

v1 では以下を正解データの元とする。

- `fixed_train_data/video-*/<cat_name>/before.png`
- `fixed_train_data/video-*/<cat_name>/after.png`
- `feature_cache/image_feature_cache.json`

---

## 8. 特徴量設計

v1 で最終的に LightGBM に入力する特徴量は、以下の 2 系統を連結したものとする。

1. 猫状態特徴量
2. 動画候補特徴量

### 8.1 猫状態特徴量

#### 8.1.1 感情分類特徴量: 3 次元

| 特徴量名 | 内容 |
|---|---|
| `emotion_happy` | 顔感情モデルの happy スコア |
| `emotion_sad` | 顔感情モデルの sad スコア |
| `emotion_angry` | 顔感情モデルの angry スコア |

補足:

- 元モデルは 7 クラス出力を持つ
- v1 では `Happy / Sad / Angry` を抽出して使う
- 他ラベルは現時点では捨てる

#### 8.1.2 ViTPose 圧縮特徴量: 12 次元

v1 では厳密な解剖学的特徴量ではなく、キーポイントの幾何学的広がりを使う。

| 特徴量名 | 意味 |
|---|---|
| `pose_mean_confidence` | キーポイント検出信頼度の平均 |
| `pose_x_span` | x 方向の広がり |
| `pose_y_span` | y 方向の広がり |
| `pose_area_ratio` | 全体の広がり面積 |
| `pose_centroid_x` | 重心 x |
| `pose_centroid_y` | 重心 y |
| `pose_pc1_variance` | 主成分 1 の分散 |
| `pose_pc2_variance` | 主成分 2 の分散 |
| `pose_pc_ratio` | 主成分分散比 |
| `pose_principal_angle_sin` | 主方向角の sin |
| `pose_principal_angle_cos` | 主方向角の cos |
| `pose_compactness` | 密集度 |

この設計を採る理由:

- 少量データでも安定して計算しやすい
- 部位ごとの厳密な対応に依存しない
- Vertex AI Endpoint 実装に落とし込みやすい

#### 8.1.3 CLIP 類似度特徴量: 8 次元

CLIP は画像そのものを最終分類するために使うのではなく、**自然言語ラベルとの意味類似度を数値特徴量として抽出するため**に使う。

v1 で採用するプロンプトは以下とする。

| 特徴量名 | プロンプト |
|---|---|
| `clip_attentive_cat` | `"attentive cat"` |
| `clip_relaxed_cat` | `"relaxed cat"` |
| `clip_stressed_cat` | `"stressed cat"` |
| `clip_playful_cat` | `"playful cat"` |
| `clip_sleepy_cat` | `"sleepy cat"` |
| `clip_curious_cat` | `"curious cat"` |
| `clip_alert_cat` | `"alert cat"` |
| `clip_comfortable_cat` | `"comfortable cat"` |

### 8.2 猫状態特徴量の合計次元

```
3 + 12 + 8 = 23 次元
```

### 8.3 動画候補特徴量

v1 では動画候補は `video_id` の one-hot で表す。

例:

- `video-1`
- `video-2`
- ...
- `video-10`

10 本の動画候補がある場合、

```
video_feature_dim = 10
```

### 8.4 なぜ one-hot を採用するか

本来は動画クエリのテキスト埋め込みを使う案もある。
ただし v1 では以下を優先する。

- 学習対象を安定させる
- デプロイ時の依存を減らす
- 学習時と推論時の feature order を単純化する

そのため、動画特徴量は v1 では one-hot とする。

### 8.5 最終入力ベクトル

動画候補数が 10 本の場合:

```
cat_state_features (23)
+ video_onehot (10)
= 33 次元
```

動画候補数が 11 本の場合:

```
23 + 11 = 34 次元
```

### 8.6 特徴量の並び順

推論時に学習時と同じ列順が必須であるため、学習成果物と一緒に feature list を保存する。

例:

```json
[
  "before_emotion_happy",
  "before_emotion_sad",
  "before_emotion_angry",
  "before_pose_mean_confidence",
  "...",
  "video_video-1",
  "video_video-2",
  "...",
  "video_video-10"
]
```

---

## 9. CLIP 類似度特徴の意味と扱い

### 9.1 CLIP は何を返しているか

CLIP は画像とテキストを同一意味空間へ写像する。
このため、猫画像と各テキストプロンプトの近さをスコア化できる。

例:

```json
{
  "clip_attentive_cat": 0.31,
  "clip_relaxed_cat": 0.05,
  "clip_stressed_cat": 0.22,
  "clip_playful_cat": 0.14
}
```

これは「その画像の猫がどの意味ラベルに近いか」を表している。

### 9.2 CLIP をどう解釈するか

CLIP 類似度は以下の補助的意味特徴として扱う。

- attentive: 画面への注目
- relaxed: 落ち着き
- stressed: 緊張・不快
- playful: 遊びたい雰囲気
- sleepy: 眠そう
- curious: 興味・探索性
- alert: 反応準備状態
- comfortable: 心地よさ

### 9.3 CLIP は最終判定モデルではない

重要なのは、CLIP は最終的な reward 予測器ではないこと。

CLIP はあくまで:

- 意味ラベルの近さを数値化する
- 感情分類やポーズでは拾いにくい状態を補う
- LightGBM Regressor に与える説明変数を増やす

ための中間特徴抽出器である。

### 9.4 将来拡張

将来的には以下を追加可能である。

- `"bored cat"`
- `"interested in moving object"`
- `"cat staring at a screen"`
- `"cat avoiding the screen"`

ただし v1 ではまず 8 プロンプトに固定する。

---

## 10. 報酬設計

### 10.1 基本式

報酬は before / after の状態差で定義する。

```
reward = score_after - score_before
```

### 10.2 score の定義

v1 では、特徴量から次のヒューリスティックな状態スコアを作る。

```python
score = (
    1.0 * emotion_happy
  - 0.7 * emotion_sad
  - 1.0 * emotion_angry
  + 0.4 * pose_area_ratio
  + 0.2 * pose_pc1_variance
  + 0.5 * clip_attentive_cat
  + 0.3 * clip_alert_cat
  + 0.2 * clip_playful_cat
)
```

### 10.3 なぜこの報酬設計にするか

この設計は完全な動物行動学モデルではないが、v1 では以下のメリットがある。

- 現在の特徴量から安定して計算可能
- before / after の差分を素直に使える
- 学習データ生成を簡素化できる

### 10.4 将来的な改善余地

v2 以降では以下を検討する。

- `clip_stressed_cat` を負特徴として明示追加
- `clip_bored` 系プロンプトの導入
- 人間アノテーションを含む reward 補正
- Optuna などによる重み最適化

---

## 11. 学習設計

### 11.1 採用学習器

```python
LightGBM Regressor
```

### 11.2 学習入出力

```
X = concat(before_features, video_onehot)
y = reward
```

### 11.3 学習パラメータの考え方

データ量が少ないため、木の複雑さは抑える。

代表例:

```python
LGBMRegressor(
    objective="regression",
    n_estimators=300,
    learning_rate=0.03,
    num_leaves=7,
    min_data_in_leaf=1,
    min_data_in_bin=1,
    max_depth=3,
    random_state=42,
)
```

### 11.4 評価方針

v1 では以下を分けて扱う。

- 学習器の fitting 確認
- 猫単位の汎化性能確認

評価設計:

- `GroupKFold` で `cat_name` 単位に分割
- MAE
- Spearman correlation
- 推奨動画 top-k の妥当性確認

### 11.5 Ranker を使わない理由

`LightGBM Ranker` は研究候補として保持するが、v1 本番モデルには採用しない。

理由:

- relevance ラベルの向き定義が繊細
- データ量が少なく不安定
- Backend に UCB があるため、まずは回帰スコアがあれば十分

---

## 12. 推論設計

### 12.1 推論の全体像

1 回の推論では 1 枚の猫画像と 0 or 1 個の音声を受ける。

Endpoint 内では以下を行う。

1. 画像から emotion / pose / clip 特徴を抽出
2. 必要なら音声から meow ラベルを抽出
3. `cat_state_features` を作成
4. 全動画候補に対して one-hot を順番に付与
5. 各候補について Regressor で `predicted_reward` を計算
6. 結果配列を Backend へ返す

責務の分割は以下で固定する。

- `model/`: base64 画像を受け取り、実モデルで `emotion / pose / clip` 特徴量を抽出する
- `model/`: `candidate_video_ids` ごとに Regressor を走らせて `predicted_rewards` を返す
- `backend/`: `predicted_rewards` を受け取り UCB を加算して最終選択する

### 12.2 推論アルゴリズム

```python
cat_features = extract_cat_features(image, audio)

predicted_rewards = []
for video_id in candidate_video_ids:
    x = concat(cat_features, one_hot(video_id))
    r = regressor.predict(x)
    predicted_rewards.append(r)

return predicted_rewards
```

### 12.3 Endpoint が返すべきもの

Endpoint は少なくとも以下を返す。

- `features`
- `predicted_rewards`
- `aux_labels`

`aux_labels` の例:

- dominant emotion
- meow label
- clip top label

これにより Backend は状態キーを組み立てやすくなる。

---

## 13. デプロイ設計

### 13.1 どこへデプロイするか

デプロイ先は **Vertex AI Custom Endpoint** である。

構成:

- `model/` ディレクトリをコンテナ化
- Artifact Registry へ push
- `script/deploy_model_endpoint.py` で Model Registry / Endpoint へ登録

### 13.2 Endpoint に含めるもの

Vertex AI Endpoint コンテナには以下を含める。

- emotion モデル
- pose モデル
- CLIP モデル
- 必要なら meow モデル
- 学習済み LightGBM Regressor
- feature order 定義ファイル
- video candidate 定義

### 13.3 Endpoint に含めないもの

以下は Endpoint に含めない。

- UCB Bandit
- Firestore アクセス
- Gemini 呼び出し
- Veo 呼び出し

これらは Backend の責務である。

### 13.4 なぜ統合 Endpoint にするか

以下のためである。

- 猫特徴抽出と reward 回帰を同一プロセスで完結できる
- Backend から 1 リクエストで必要なスコアを取得できる
- 推論レイテンシを抑えやすい

### 13.5 Endpoint の返却値と Backend の関係

Endpoint:

```json
{
  "predicted_rewards": {
    "video-1": -0.12,
    "video-2": 0.44,
    "video-3": 0.08
  }
}
```

Backend:

```python
final_score = predicted_reward + ucb_bonus
selected_video = argmax(final_score)
```

---

## 14. 入出力スキーマ

### 14.1 Endpoint 入力

```json
{
  "image_base64": "<base64>",
  "audio_base64": "<base64 or null>",
  "candidate_video_ids": [
    "video-1",
    "video-2",
    "video-3",
    "video-4",
    "video-5",
    "video-6",
    "video-7",
    "video-8",
    "video-9",
    "video-10"
  ]
}
```

### 14.2 Endpoint 出力

```json
{
  "features": {
    "emotion_happy": 0.18,
    "emotion_sad": 0.11,
    "emotion_angry": 0.05,
    "pose_area_ratio": 0.39,
    "clip_attentive_cat": 0.28
  },
  "aux_labels": {
    "emotion_label": "happy",
    "clip_top_label": "attentive_cat",
    "meow_label": "waiting_for_food"
  },
  "predicted_rewards": {
    "video-1": -0.22,
    "video-2": 0.31,
    "video-3": 0.05,
    "video-4": 0.42,
    "video-5": 0.37,
    "video-6": 0.28,
    "video-7": -0.03,
    "video-8": 0.16,
    "video-9": 0.21,
    "video-10": -0.44
  }
}
```

### 14.3 Backend 側の利用

Backend はこのレスポンスを受けて:

- `state_key` を組み立てる
- Firestore の bandit_table を読む
- `predicted_rewards + UCB_bonus` で最終選択する

---

## 15. 学習成果物

学習後に保存すべき成果物は以下。

| ファイル | 内容 |
|---|---|
| `reward_regressor.joblib` | 学習済み LightGBM Regressor |
| `feature_columns.json` | 学習時の特徴量順序 |
| `video_id_mapping.json` | 動画候補一覧 |
| `training_metadata.json` | 学習日時、データ件数、使用モデル ID、reward 設計 |
| `clip_prompts.json` | 使用した CLIP プロンプト |

### 15.1 なぜ feature_columns を保存するか

LightGBM は列順がズレると推論結果が壊れる。
そのため、学習時と同じ順序を必ず再現できるようにする。

### 15.2 metadata に含めるべき内容

```json
{
  "version": "v1",
  "emotion_model_id": "semihdervis/cat-emotion-classifier",
  "pose_model_id": "usyd-community/vitpose-plus-small",
  "clip_model_id": "openai/clip-vit-base-patch32",
  "regressor_type": "lightgbm_regressor",
  "candidate_video_count": 10,
  "reward_formula_version": "reward_v1"
}
```

---

## 16. 実装責務の分割

### 16.1 `tea-pillar-ML-analysis` 側

責務:

- 正解データ整形
- 特徴量キャッシュ生成
- 学習 notebook / script
- モデル評価
- 学習済み成果物出力

### 16.2 `tea-pillar` 側 `model/`

責務:

- Vertex AI で動く predictor 実装
- 学習済み成果物のロード
- 推論 API 実装
- Docker 化

### 16.3 `tea-pillar` 側 `backend/`

責務:

- Endpoint 呼び出し
- UCB
- Firestore
- Gemini / Veo
- API レスポンス

---

## 17. 開発・検証フロー

### 17.1 学習フロー

1. `fixed_train_data` を準備
2. `precompute_image_features.py` で特徴量 JSON を作る
3. `pattern_b_reward_ranking.ipynb` 相当の学習処理で Regressor を学習
4. 学習済み成果物を保存

### 17.2 デプロイフロー

1. 学習済み成果物を `model/artifacts/` に配置
2. `model/Dockerfile` で Vertex AI 推論コンテナをビルド
3. Artifact Registry へ push
4. `script/deploy_model_endpoint.py` で Endpoint へデプロイ
5. `script/test_endpoint.py` で動作確認

補足:

- `tea-pillar` 側では `scripts/deploy_ML/export_pattern_b_artifacts.py` を用意しており、
  `pattern_b/session_feature_table.csv` から `reward_regressor.joblib` と各種 JSON を
  `model/artifacts/` へ出力できる状態にしている
- `model/` は現在 `/predict`, `/health` を持つ FastAPI app 構成で実装されている

### 17.3 推奨する検証項目

- 1 リクエストで全動画候補分の reward が返ること
- 学習時と同じ feature order で推論できること
- image_base64 が同じなら再現性のある予測になること
- 主要動画候補のスコア順が期待と大きく矛盾しないこと
- `reward_regressor.joblib` 読み込み時に fallback へ落ちていないこと

---

## 18. v1 の制約と既知のズレ

### 18.1 docs 上の旧記述との差分

v1 では以下を採用する。

- ViTPose: `usyd-community/vitpose-plus-small`
- 最終モデル: `LightGBM Regressor`
- 動画特徴量: one-hot
- CLIP: 8 プロンプト固定

したがって、旧案である以下とは異なる。

- `vitpose-plus-plus-small`
- LightGBM Ranker 本番採用
- 動画クエリ埋め込み + PCA を必須化
- 高度な pose 工学特徴

### 18.2 学習データ量の制約

現状は猫数・セッション数が少ないため、

- 汎化性能はまだ高くない
- まずは PoC / デモ向けの v1 として扱う
- 継続的に追加データで再学習する前提とする

### 18.3 音声特徴の扱い

v1 学習は画像中心で進めている。
音声モデルは将来的に `cat_state_features` へ統合する前提だが、初期デプロイでは optional とする。

---

## 19. 今後の拡張方針

### 19.1 v2 の有力候補

- 動画特徴量を one-hot から CLIP テキスト埋め込みへ移行
- `LightGBM Ranker` を比較再評価
- 人手ラベルを使った reward 補正
- pose 特徴量の意味的再設計
- meow 特徴量の本格統合

### 19.2 それでも v1 を先に出す理由

v1 は以下を満たしている。

- 既存 HF モデル群と整合
- 学習済み成果物を保存・再利用しやすい
- Vertex AI Endpoint へ実際に載せやすい
- Backend の UCB 設計と矛盾しない

したがって、**この v1 設計をベースにまずデプロイを成立させ、その後に段階的改善を行う**ことを推奨する。
