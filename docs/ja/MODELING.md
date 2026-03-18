# MODELING.md
## モデル設計書 — パターンB：報酬回帰 + ランキング（LightGBM Ranker / LambdaMART）

---

## 目次

1. [コンセプト](#1-コンセプト)
2. [データ構造](#2-データ構造)
3. [特徴量設計](#3-特徴量設計)
   - 3.1 [猫状態特徴量（before）](#31-猫状態特徴量before)
   - 3.2 [動画クエリ特徴量](#32-動画クエリ特徴量)
   - 3.3 [最終的な入力ベクトル](#33-最終的な入力ベクトル)
4. [報酬設計](#4-報酬設計)
5. [学習設計](#5-学習設計)
   - 5.1 [アプローチ①：reward回帰（LightGBM Regressor）](#51-アプローチ①reward回帰lightgbm-regressor)
   - 5.2 [アプローチ②：Learning to Rank（LightGBM Ranker）](#52-アプローチ②learning-to-ranklightgbm-ranker)
   - 5.3 [採用アプローチの選定基準](#53-採用アプローチの選定基準)
6. [検証設計](#6-検証設計)
7. [推論フロー](#7-推論フロー)
8. [JSONデータ構造とパイプライン実装](#8-jsonデータ構造とパイプライン実装)
   - 8.1 [学習データのJSON構造](#81-学習データのjson構造)
   - 8.2 [特徴量抽出パイプライン](#82-特徴量抽出パイプライン)
   - 8.3 [DataFrameへの変換](#83-dataframeへの変換)
9. [ViTPoseキーポイント → 角度特徴量への変換](#9-vitposeキーポイント--角度特徴量への変換)
10. [CLIPプロンプト設計](#10-clipプロンプト設計)
11. [未決定事項（TBD）](#11-未決定事項tbd)

---

## 1. コンセプト

猫の状態（before特徴量）と動画クエリの組み合わせに対して **reward（猫の反応変化量）を回帰予測** し、推論時に全11本の予測rewardをスコアリングして最良の1本を返す。

```
入力: (猫のbefore状態特徴量) × (動画クエリ特徴量)
      ↓
学習: reward を予測するLightGBMモデル
      ↓
推論: 全11クエリを総当たりでスコアリング → 最高スコアのクエリIDを返す
```

**パターンAとの主な違い：**
- rewardをハードラベル（argmax）に変換せず、**連続値のままフル活用**する
- 動画クエリをfeatureとして入力に含めるため、**未知クエリへの転移**が可能
- 動画間の相対的な優劣を学習するため、**ランキング精度が高い**

---

## 2. データ構造

学習データの1行は「**1猫 × 1動画 × 1セッション**」の組み合わせ。

11本の動画を1匹の猫に見せると 11行 が生成される。これが基本ユニット。

```
cat_A × video_00 × session_1  →  reward: -0.12
cat_A × video_01 × session_1  →  reward: +0.45
cat_A × video_02 × session_1  →  reward: +0.03
...
cat_A × video_10 × session_1  →  reward: +0.31
```

| 変数 | 内容 |
|------|------|
| `cat_id` | 猫の識別子（グループ分割・CV用） |
| `session_id` | セッションの識別子（1セッション = before撮影 → 動画視聴 → after撮影） |
| `video_id` | 動画クエリID（0〜10） |
| `before_features` | 猫状態特徴量ベクトル（セクション3.1参照） |
| `video_features` | 動画クエリ特徴量ベクトル（セクション3.2参照） |
| `reward` | 目的変数：動画視聴後の猫の状態変化スコア（セクション4参照） |
| `human_label` | 人間によるアノテーションラベル（0/1、オプション） |

---

## 3. 特徴量設計

### 3.1 猫状態特徴量（before）

動画視聴**前**の猫画像から以下3モデルで抽出する。

#### ① 顔感情スコア（3次元）

| 特徴量名 | 内容 | 取得モデル |
|---------|------|----------|
| `emo_happy` | happy確率 | `semihdervis/cat-emotion-classifier` |
| `emo_sad` | sad確率 | 同上 |
| `emo_angry` | angry確率 | 同上 |

#### ② ViTPose++ 姿勢角度（12次元）

生のキーポイント座標（51次元）を意味ある角度・比率に圧縮する。
変換ロジックの詳細は [セクション9](#9-vitposeキーポイント--角度特徴量への変換) 参照。

| 特徴量名 | 内容 | 算出方法 |
|---------|------|---------|
| `pose_ear_left_angle` | 左耳の立ち角度 | 耳キーポイントの垂直方向角度 |
| `pose_ear_right_angle` | 右耳の立ち角度 | 同上（右） |
| `pose_ear_symmetry` | 両耳の非対称度 | 左右角度差の絶対値 |
| `pose_tail_angle` | 尻尾の立ち上がり角度 | 尻尾根元〜先端の垂直角度 |
| `pose_spine_curve` | 脊椎の丸まり度 | 首・背中・腰のキーポイントで計算した曲率 |
| `pose_head_tilt` | 頭の傾き | 頭部と体軸のなす角度 |
| `pose_body_compactness` | 体の丸まり・コンパクト度 | バウンディングボックスの縦横比 |
| `pose_activity_score` | 活発度スコア | 主要キーポイントの信頼度加重平均 |
| `pose_forepaw_spread` | 前足の開き具合 | 左右前足キーポイントの距離 |
| `pose_hindpaw_spread` | 後足の開き具合 | 左右後足キーポイントの距離 |
| `pose_nose_height` | 鼻の高さ（頭上げ具合） | 鼻キーポイントのy座標正規化値 |
| `pose_keypoint_conf_mean` | 全キーポイントの平均信頼度 | 17点のconfidence平均 |

#### ③ CLIPゼロショットスコア（8次元）

カスタムプロンプトとの類似度スコア。プロンプト一覧は [セクション10](#10-clipプロンプト設計) 参照。

| 特徴量名 | プロンプト |
|---------|----------|
| `clip_attentive` | `"a cat looking attentively at a screen"` |
| `clip_relaxed` | `"a relaxed and calm cat"` |
| `clip_stressed` | `"a stressed or anxious cat"` |
| `clip_playful` | `"a playful and curious cat"` |
| `clip_sleepy` | `"a sleepy or drowsy cat"` |
| `clip_alert` | `"an alert cat with ears up"` |
| `clip_content` | `"a content and comfortable cat"` |
| `clip_bored` | `"a bored or disinterested cat"` |

---

### 3.2 動画クエリ特徴量

動画クエリをfeatureとして入力に含めることで、未知クエリへの転移と「どのクエリがどんな猫に向くか」のパターン学習を可能にする。

#### 方式：CLIPテキストエンコーダーによるembedding

11本のクエリテキストを `openai/clip-vit-base-patch32` のテキストエンコーダーで512次元のベクトルに変換し、PCAで16次元に圧縮する。

```python
from transformers import CLIPModel, CLIPTokenizer
import torch

model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
tokenizer = CLIPTokenizer.from_pretrained("openai/clip-vit-base-patch32")

QUERY_TEXTS = [
    "playful yarn ball bouncing in sunlight",         # video_00
    "colorful fish swimming in an aquarium",          # video_01
    "bird flying slowly across a blue sky",           # video_02
    "laser dot moving erratically on a floor",        # video_03
    "rustling leaves and gentle wind in a forest",    # video_04
    "small mouse running across a wooden floor",      # video_05
    "butterflies floating in a flower garden",        # video_06
    "dragonfly hovering near water surface",          # video_07
    "feather wand swinging slowly back and forth",    # video_08
    "bubbles floating upward in calm water",          # video_09
    "crackling fireplace with soft flickering light", # video_10
]

def get_query_embedding(text: str) -> torch.Tensor:
    inputs = tokenizer(text, return_tensors="pt", padding=True)
    with torch.no_grad():
        embedding = model.get_text_features(**inputs)
    return embedding / embedding.norm(dim=-1, keepdim=True)  # L2正規化

# 事前に全11本のembeddingを計算・保存
query_embeddings = {
    i: get_query_embedding(text).squeeze().numpy()
    for i, text in enumerate(QUERY_TEXTS)
}
```

> **Note:** query_embeddingはPCAで16次元に圧縮する前提。圧縮後の次元数は検証で決定（TBD）。

---

### 3.3 最終的な入力ベクトル

| グループ | 特徴量 | 次元数 |
|---------|-------|-------|
| 顔感情スコア（before） | `emo_*` × 3 | 3 |
| 姿勢角度（before） | `pose_*` × 12 | 12 |
| CLIPゼロショットスコア（before） | `clip_*` × 8 | 8 |
| 動画クエリembedding | PCA圧縮後 | 16 |
| **合計** | | **39次元** |

---

## 4. 報酬設計

### 報酬の定義

```
reward(session) = score_after − score_before
```

### スコア計算式

```python
def compute_score(features: dict, weights: dict) -> float:
    score = (
        weights['w_happy']      * features['emo_happy']
      - weights['w_sad']        * features['emo_sad']
      - weights['w_angry']      * features['emo_angry']
      + weights['w_activity']   * features['pose_activity_score']
      + weights['w_attentive']  * features['clip_attentive']
      - weights['w_stressed']   * features['clip_stressed']
      - weights['w_bored']      * features['clip_bored']
    )
    return score
```

### デフォルト重み（初期値）

| 重み | デフォルト値 | 説明 |
|------|------------|------|
| `w_happy` | 1.0 | happyは強くポジティブ |
| `w_sad` | 0.8 | sadはネガティブ |
| `w_angry` | 1.0 | angryは強くネガティブ |
| `w_activity` | 0.5 | 活発度は中程度でポジティブ |
| `w_attentive` | 0.8 | 画面注目はポジティブ |
| `w_stressed` | 0.7 | ストレスはネガティブ |
| `w_bored` | 0.6 | 退屈はネガティブ |

> **重みの調整方針：** デフォルト値はヒューリスティックな初期値。人間によるアノテーション（`human_label`）と reward の相関を確認しながら調整する。最終的には Optuna 等でハイパーパラメータ最適化することも検討（TBD）。

### rewardの値域

| reward | 解釈 |
|--------|------|
| `> +0.3` | 明確にポジティブな反応（テンション上がった） |
| `-0.1 〜 +0.3` | 中立・わずかな変化 |
| `< -0.1` | ネガティブ or 無反応 |

---

## 5. 学習設計

### 5.1 アプローチ①：reward回帰（LightGBM Regressor）

猫状態 × 動画クエリの組み合わせごとに reward を直接回帰予測する。

```
入力 X: (before_features + video_embedding) shape: (n_samples, 39)
目的変数 y: reward shape: (n_samples,)  ← 連続値
```

```python
import lightgbm as lgb
from sklearn.model_selection import GroupKFold

model = lgb.LGBMRegressor(
    objective='regression',
    metric='mae',
    num_leaves=31,
    learning_rate=0.05,
    n_estimators=300,
    min_child_samples=5,   # データ少量対策
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
)
```

**評価指標：**
- MAE（平均絶対誤差）：rewardの予測精度
- Spearman相関係数：11本の動画を正しくランキングできているか
- Top-1 Accuracy：予測best動画が真のbest動画と一致する割合

---

### 5.2 アプローチ②：Learning to Rank（LightGBM Ranker）

1匹の猫の1セッション（11行）を1グループとして、相対的なランキングを学習する。rewardの**絶対値ではなく順位関係**に特化して最適化する。

```
入力 X:     (before_features + video_embedding) shape: (n_samples, 39)
目的変数 y: rewardを順位に変換したrank score shape: (n_samples,)
groups:     1セッション = 11行 のグループサイズ配列
```

```python
import lightgbm as lgb
import numpy as np

# rewardを0〜10の整数ランクに変換（同一セッション内で相対ランク付け）
def reward_to_rank(rewards_in_session: np.ndarray) -> np.ndarray:
    # 降順ランク（rewardが高い動画ほど高ランク）
    return rewards_in_session.argsort().argsort()

model = lgb.LGBMRanker(
    objective='lambdarank',
    metric='ndcg',
    ndcg_eval_at=[1, 3],   # NDCG@1, NDCG@3 で評価
    num_leaves=31,
    learning_rate=0.05,
    n_estimators=300,
    min_child_samples=5,
    random_state=42,
)

model.fit(
    X_train,
    y_rank_train,
    group=group_sizes_train,         # 各セッションのサイズ（11固定）
    eval_set=[(X_val, y_rank_val)],
    eval_group=[group_sizes_val],
    callbacks=[lgb.early_stopping(50), lgb.log_evaluation(50)],
)
```

**評価指標：**
- NDCG@1：最良の動画を1位に選べているか
- NDCG@3：上位3本の質
- Top-1 Accuracy（参考値）

---

### 5.3 採用アプローチの選定基準

| 条件 | 採用アプローチ |
|------|-------------|
| データ量が少ない（< 100セッション） | アプローチ①（Regressor）を優先。Rankerはグループ数が少ないと不安定。 |
| データ量が十分（≥ 100セッション） | アプローチ②（Ranker）を優先。相対ランキング精度が高い。 |
| 両方検証可能な場合 | NDCG@1とTop-1 Accuracyで比較し、高い方を本番採用。 |

> **初期方針：** まずアプローチ①で動くモデルを作り、データが積み上がったタイミングでアプローチ②に移行・比較する。

---

## 6. 検証設計

### Leave-one-cat-out Cross Validation

データが少ない状況での汎化性評価に最も適した方法。特定の猫でのみ学習し、別の猫で評価することで、「見たことのない猫にも機能するか」を検証する。

```python
from sklearn.model_selection import GroupKFold
import numpy as np

cat_ids = df['cat_id'].values
gkf = GroupKFold(n_splits=len(np.unique(cat_ids)))  # 猫の数 = fold数

results = []
for fold, (train_idx, val_idx) in enumerate(gkf.split(X, y, groups=cat_ids)):
    X_train, X_val = X[train_idx], X[val_idx]
    y_train, y_val = y[train_idx], y[val_idx]
    
    model.fit(X_train, y_train)
    
    # セッション単位でTop-1 Accuracyを評価
    for session_id in df.loc[val_idx, 'session_id'].unique():
        mask = df.loc[val_idx, 'session_id'] == session_id
        scores = model.predict(X_val[mask])
        pred_best = np.argmax(scores)
        true_best = np.argmax(y_val[mask])
        results.append({'fold': fold, 'correct': int(pred_best == true_best)})

top1_acc = np.mean([r['correct'] for r in results])
print(f"Leave-one-cat-out Top-1 Accuracy: {top1_acc:.3f}")
```

### 評価指標サマリー

| 指標 | 計算対象 | 目標値（目安） |
|------|---------|-------------|
| Top-1 Accuracy | セッション単位：予測1位 = 真の1位 | > 0.4（11クラスランダムは0.09） |
| Top-3 Accuracy | セッション単位：真の1位が予測上位3位以内 | > 0.7 |
| NDCG@1 | セッション単位（Rankerのみ） | > 0.6 |
| Spearman相関 | セッション内の動画ランキング順位相関 | > 0.3 |
| MAE | rewardの予測誤差（Regressorのみ） | データ分布に依存 |

---

## 7. 推論フロー

実際のnekkoflixでの使われ方に沿ったエンドツーエンドの推論手順。

```
Step 1: before画像を受け取る
         ↓
Step 2: 3モデルで特徴量抽出
         emotion_probs  = cat_emotion_model(image)      # 3次元
         keypoints      = vitpose_model(image)           # 51次元
         pose_angles    = compute_angles(keypoints)      # 12次元
         clip_scores    = clip_model(image, PROMPTS)     # 8次元
         before_vec     = concat([emotion_probs, pose_angles, clip_scores])  # 23次元
         ↓
Step 3: 全11クエリを総当たりでスコアリング
         scores = []
         for video_id in range(11):
             x = concat([before_vec, query_embeddings[video_id]])  # 39次元
             scores.append(model.predict(x))
         ↓
Step 4: 最高スコアのクエリIDを返す
         best_id  = argmax(scores)         # ハード出力（1本）
         top3_ids = argsort(scores)[-3:]   # ソフト出力（上位3本）
         ↓
Step 5: Geminiに投げる
         gemini_input = {
             "template": QUERY_TEXTS[best_id],
             "cat_state": state_key,
             "user_context": user_context,  # オーナーが設定した猫の好み・性格
         }
```

### 出力形式まとめ

| 出力 | 形式 | 用途 |
|------|------|------|
| `best_id` | int（0〜10） | Bandit層・Geminiへの入力（1本決定） |
| `top3_ids` | list[int] | Geminiに候補を複数渡す場合 |
| `scores` | list[float]（11次元） | Banditテーブルの更新・探索に使う場合 |

---

## 8. JSONデータ構造とパイプライン実装

### 8.1 学習データのJSON構造

```json
{
  "session_id": "s001",
  "cat_id": "cat_A",
  "video_id": 3,
  "before": {
    "emotion": [0.72, 0.15, 0.13],
    "pose_angles": [12.3, 45.1, 8.7, 33.2, 0.82, 15.4, 0.67, 0.91, 28.3, 22.1, 0.44, 0.88],
    "clip_scores": [0.81, 0.34, 0.22, 0.71, 0.12, 0.65, 0.55, 0.18]
  },
  "after": {
    "emotion": [0.88, 0.07, 0.05],
    "pose_angles": [25.4, 72.3, 15.2, 41.0, 0.90, 20.1, 0.74, 0.94, 35.6, 30.0, 0.51, 0.93],
    "clip_scores": [0.91, 0.21, 0.18, 0.80, 0.09, 0.74, 0.63, 0.11]
  },
  "reward": 0.43,
  "human_label": 1
}
```

### 8.2 特徴量抽出パイプライン

```python
from transformers import (
    pipeline,
    AutoImageProcessor,
    VitPoseForPoseEstimation,
    CLIPModel,
    CLIPProcessor,
)
from PIL import Image
import torch
import numpy as np

# モデルのロード（起動時に1回）
emotion_pipeline = pipeline(
    "image-classification",
    model="semihdervis/cat-emotion-classifier"
)

vitpose_processor = AutoImageProcessor.from_pretrained(
    "usyd-community/vitpose-plus-plus-small"
)
vitpose_model = VitPoseForPoseEstimation.from_pretrained(
    "usyd-community/vitpose-plus-plus-small"
)

clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

CLIP_PROMPTS = [
    "a cat looking attentively at a screen",
    "a relaxed and calm cat",
    "a stressed or anxious cat",
    "a playful and curious cat",
    "a sleepy or drowsy cat",
    "an alert cat with ears up",
    "a content and comfortable cat",
    "a bored or disinterested cat",
]


def extract_emotion(image: Image.Image) -> list[float]:
    results = emotion_pipeline(image)
    label_map = {"happy": 0, "sad": 1, "angry": 2}
    probs = [0.0, 0.0, 0.0]
    for r in results:
        idx = label_map.get(r["label"].lower())
        if idx is not None:
            probs[idx] = r["score"]
    return probs  # [p_happy, p_sad, p_angry]


def extract_pose_angles(image: Image.Image) -> list[float]:
    inputs = vitpose_processor(images=image, return_tensors="pt")
    with torch.no_grad():
        outputs = vitpose_model(**inputs, dataset_index=torch.tensor([3]))
    keypoints = outputs.keypoints[0].numpy()  # shape: (17, 3) = (x, y, conf)
    return compute_angles(keypoints)           # 12次元に圧縮（セクション9参照）


def extract_clip_scores(image: Image.Image) -> list[float]:
    inputs = clip_processor(
        text=CLIP_PROMPTS,
        images=image,
        return_tensors="pt",
        padding=True,
    )
    with torch.no_grad():
        outputs = clip_model(**inputs)
    logits = outputs.logits_per_image[0]
    scores = logits.softmax(dim=-1).tolist()
    return scores  # 8次元


def extract_features(image_path: str) -> dict:
    image = Image.open(image_path).convert("RGB")
    return {
        "emotion":     extract_emotion(image),
        "pose_angles": extract_pose_angles(image),
        "clip_scores": extract_clip_scores(image),
    }


def compute_reward(before: dict, after: dict, weights: dict = None) -> float:
    if weights is None:
        weights = {
            "w_happy": 1.0, "w_sad": 0.8, "w_angry": 1.0,
            "w_activity": 0.5, "w_attentive": 0.8,
            "w_stressed": 0.7, "w_bored": 0.6,
        }

    def score(f):
        return (
            weights["w_happy"]     * f["emotion"][0]
          - weights["w_sad"]       * f["emotion"][1]
          - weights["w_angry"]     * f["emotion"][2]
          + weights["w_activity"]  * f["pose_angles"][7]   # pose_activity_score
          + weights["w_attentive"] * f["clip_scores"][0]   # clip_attentive
          - weights["w_stressed"]  * f["clip_scores"][2]   # clip_stressed
          - weights["w_bored"]     * f["clip_scores"][7]   # clip_bored
        )

    return score(after) - score(before)
```

### 8.3 DataFrameへの変換

```python
import pandas as pd
import json

FEATURE_COLS = (
    ["emo_happy", "emo_sad", "emo_angry"]
    + [f"pose_{i}" for i in range(12)]
    + [f"clip_{i}" for i in range(8)]
    + [f"query_emb_{i}" for i in range(16)]  # PCA圧縮後
)


def session_to_rows(session: dict, query_embeddings_pca: dict) -> list[dict]:
    """1セッションのJSONを、全11動画分の行リストに展開する"""
    before = session["before"]
    base_vec = (
        before["emotion"]
        + before["pose_angles"]
        + before["clip_scores"]
    )
    rows = []
    for video_id in range(11):
        query_emb = query_embeddings_pca[video_id].tolist()
        row = {
            "session_id": session["session_id"],
            "cat_id":     session["cat_id"],
            "video_id":   video_id,
            "reward":     session["reward"] if session["video_id"] == video_id else None,
        }
        # ※ rewardはそのsessionで実際に見せた動画のみ記録されているため、
        #    未実測の動画はNoneとし、学習データから除外する
        feat = dict(zip(FEATURE_COLS, base_vec + query_emb))
        row.update(feat)
        rows.append(row)
    return [r for r in rows if r["reward"] is not None]


def build_dataframe(sessions: list[dict], query_embeddings_pca: dict) -> pd.DataFrame:
    all_rows = []
    for s in sessions:
        all_rows.extend(session_to_rows(s, query_embeddings_pca))
    return pd.DataFrame(all_rows)
```

---

## 9. ViTPoseキーポイント → 角度特徴量への変換

AP-10K headのキーポイント定義（17点）から12次元の角度特徴量を計算する。

```
AP-10K 17キーポイント定義（猫）:
 0: 鼻 (nose)
 1: 左目 (left_eye)
 2: 右目 (right_eye)
 3: 左耳根元 (left_ear_base)
 4: 右耳根元 (right_ear_base)
 5: 左肩 (left_shoulder)
 6: 右肩 (right_shoulder)
 7: 左前足首 (left_front_paw)
 8: 右前足首 (right_front_paw)
 9: 腰左 (left_hip)
10: 腰右 (right_hip)
11: 左後足首 (left_rear_paw)
12: 右後足首 (right_rear_paw)
13: 尻尾根元 (tail_base)
14: 尻尾中間 (tail_mid)
15: 尻尾先端 (tail_tip)
16: 背中中央 (spine_mid)
```

```python
import numpy as np

def compute_angles(kp: np.ndarray) -> list[float]:
    """
    kp: shape (17, 3) = (x, y, confidence)
    returns: 12次元の角度・比率特徴量
    """
    def angle_from_vertical(p1, p2):
        """2点を結ぶベクトルと垂直軸のなす角度（度）"""
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        return np.degrees(np.arctan2(abs(dx), abs(dy) + 1e-6))

    def dist(p1, p2):
        return np.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

    nose, l_eye, r_eye = kp[0], kp[1], kp[2]
    l_ear, r_ear = kp[3], kp[4]
    l_sho, r_sho = kp[5], kp[6]
    l_fpaw, r_fpaw = kp[7], kp[8]
    l_hip, r_hip = kp[9], kp[10]
    l_rpaw, r_rpaw = kp[11], kp[12]
    tail_base, tail_mid, tail_tip = kp[13], kp[14], kp[15]
    spine_mid = kp[16]

    body_center = (l_sho + r_sho + l_hip + r_hip) / 4

    # 1. 左耳の立ち角度
    ear_left_angle  = angle_from_vertical(l_ear, nose)
    # 2. 右耳の立ち角度
    ear_right_angle = angle_from_vertical(r_ear, nose)
    # 3. 耳の非対称度
    ear_symmetry    = abs(ear_left_angle - ear_right_angle)
    # 4. 尻尾の立ち上がり角度
    tail_angle      = angle_from_vertical(tail_base, tail_tip)
    # 5. 脊椎の丸まり度（鼻→背中→尻尾の曲率）
    spine_curve     = angle_from_vertical(nose, spine_mid) + angle_from_vertical(spine_mid, tail_base)
    # 6. 頭の傾き（体軸に対する頭の角度）
    head_tilt       = angle_from_vertical(body_center[:2], nose[:2])
    # 7. 体のコンパクト度（縦横比）
    body_h = abs(nose[1] - tail_base[1]) + 1e-6
    body_w = dist(l_sho, r_sho) + 1e-6
    body_compactness = body_w / body_h
    # 8. 活発度スコア（キーポイント信頼度の加重平均）
    activity_score  = float(np.mean(kp[:, 2]))
    # 9. 前足の開き具合
    forepaw_spread  = dist(l_fpaw, r_fpaw) / (body_w + 1e-6)
    # 10. 後足の開き具合
    hindpaw_spread  = dist(l_rpaw, r_rpaw) / (body_w + 1e-6)
    # 11. 鼻の高さ（頭上げ具合、y座標を正規化）
    nose_height     = float((body_center[1] - nose[1]) / (body_h + 1e-6))
    # 12. 全キーポイントの平均信頼度
    kp_conf_mean    = float(np.mean(kp[:, 2]))

    return [
        ear_left_angle, ear_right_angle, ear_symmetry,
        tail_angle, spine_curve, head_tilt,
        body_compactness, activity_score,
        forepaw_spread, hindpaw_spread,
        nose_height, kp_conf_mean,
    ]
```

---

## 10. CLIPプロンプト設計

### 採用プロンプト一覧

| インデックス | プロンプト | 狙い |
|------------|----------|------|
| 0 | `"a cat looking attentively at a screen"` | 画面への注目度（最重要） |
| 1 | `"a relaxed and calm cat"` | リラックス度 |
| 2 | `"a stressed or anxious cat"` | ストレス・不安（ネガティブ） |
| 3 | `"a playful and curious cat"` | 好奇心・遊び心 |
| 4 | `"a sleepy or drowsy cat"` | 眠気・無関心 |
| 5 | `"an alert cat with ears up"` | 警戒・注意（中立〜ポジティブ） |
| 6 | `"a content and comfortable cat"` | 満足・快適 |
| 7 | `"a bored or disinterested cat"` | 退屈・無関心（ネガティブ） |

### プロンプト選定の方針

- **before/after 両方**に同じプロンプトを適用し、差分（delta）を報酬計算に使う
- プロンプトは定期的に見直す（TBD：検証後に追加・削除を検討）
- 体験モードでの「あなたが猫」設定にも同プロンプトを流用する

---

## 11. 未決定事項（TBD）

| # | 項目 | 内容 | 優先度 |
|---|------|------|-------|
| TBD-1 | rewardの重み最適化 | w1〜w7のチューニング方法（Optunaによる自動最適化 vs 手動調整） | 高 |
| TBD-2 | アプローチ①②の切り替え判断 | データ量が何セッションを超えたらRankerに移行するか | 高 |
| TBD-3 | query embeddingのPCA次元数 | 16次元が妥当かどうかを分散説明率で検証 | 中 |
| TBD-4 | AP-10Kキーポイント定義の確認 | 実際のモデル出力でのキーポイントIDとインデックスの対応を実機確認 | 高 |
| TBD-5 | 未実測動画の扱い | 1セッションで見せなかった動画のrewardの補完方法（除外 vs 補間） | 中 |
| TBD-6 | rewardのNone処理 | 全動画分のrewardが揃わない場合のDataFrame構築方法 | 中 |
| TBD-7 | CLIPプロンプトの検証 | 実際の猫画像に対してプロンプトが期待通りに機能するか確認 | 高 |