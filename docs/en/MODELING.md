# MODELING.md
## Model Design Document — Pattern B: Reward Regression + Ranking (LightGBM Ranker / LambdaMART)

---

## Table of Contents

1. Concept
2. Data Structure
3. Feature Design
4. Reward Design
5. Training Design
6. Validation Design
7. Inference Flow
8. JSON Structure and Pipeline Implementation
9. ViTPose Keypoints -> Angle Features
10. CLIP Prompt Design
11. TBD

---

## 1. Concept

For each combination of the cat's current state and a video query, predict the **reward** (the amount of change in the cat's reaction) as a continuous value. At inference time, score all 11 candidate videos and return the best one.

```text
Input: cat before-state features × video-query features
      ↓
Training: LightGBM model that predicts reward
      ↓
Inference: score all 11 queries exhaustively -> return the query ID with the highest score
```

### Main differences from Pattern A

- Reward is not converted into a hard label such as `argmax`; continuous values are used directly.
- Because the video query itself is part of the input features, transfer to unseen queries is possible.
- Relative superiority among videos can be learned, improving ranking quality.

---

## 2. Data Structure

Each training row represents one combination of **1 cat × 1 video × 1 session**.

| Variable | Content |
|------|------|
| `cat_id` | Cat identifier used for grouping and cross-validation |
| `session_id` | Session identifier |
| `video_id` | Video query ID (`0` to `10`) |
| `before_features` | Cat state feature vector before viewing |
| `video_features` | Video query feature vector |
| `reward` | Target value: score representing change in state after viewing |
| `human_label` | Optional human annotation label (`0/1`) |

---

## 3. Feature Design

### 3.1 Cat-state features (before)

Extracted from an image of the cat **before** video playback.

#### 1. Facial emotion scores (3 dimensions)

- `emo_happy`
- `emo_sad`
- `emo_angry`

Model: `semihdervis/cat-emotion-classifier`

#### 2. ViTPose++ pose-angle features (12 dimensions)

Raw keypoint coordinates are compressed into meaningful angles and ratios, including:

- left/right ear angles
- ear symmetry
- tail angle
- spine curvature
- head tilt
- body compactness
- activity score
- forepaw and hindpaw spread
- nose height
- mean keypoint confidence

#### 3. CLIP zero-shot scores (8 dimensions)

Similarity scores to custom prompts such as:

- `a cat looking attentively at a screen`
- `a relaxed and calm cat`
- `a stressed or anxious cat`
- `a playful and curious cat`
- `a sleepy or drowsy cat`
- `an alert cat with ears up`
- `a content and comfortable cat`
- `a bored or disinterested cat`

### 3.2 Video query features

Use the video query itself as an input feature so the model can learn what kind of query matches what kind of cat.

#### Method: CLIP text-encoder embeddings

The 11 query texts are embedded with `openai/clip-vit-base-patch32`, then compressed by PCA from 512 dimensions to 16 dimensions.

### 3.3 Final input vector

| Group | Features | Dimensions |
|---------|-------|-------|
| Facial emotion | `emo_*` | 3 |
| Pose angles | `pose_*` | 12 |
| CLIP zero-shot scores | `clip_*` | 8 |
| Video-query embedding | PCA-compressed | 16 |
| **Total** |  | **39** |

---

## 4. Reward Design

### Reward definition

```text
reward(session) = score_after - score_before
```

### Score computation

The score is a weighted sum of emotion, activity, attentive state, stress, and boredom, for example:

- positive: `emo_happy`, `pose_activity_score`, `clip_attentive`
- negative: `emo_sad`, `emo_angry`, `clip_stressed`, `clip_bored`

### Default weights

Typical initial defaults:

- `w_happy = 1.0`
- `w_sad = 0.8`
- `w_angry = 1.0`
- `w_activity = 0.5`
- `w_attentive = 0.8`
- `w_stressed = 0.7`
- `w_bored = 0.6`

These are heuristic starting values and will later be adjusted using correlations with human labels and possibly optimized with tools such as Optuna.

### Reward range interpretation

| Reward | Interpretation |
|--------|------|
| `> +0.3` | Clearly positive reaction |
| `-0.1 to +0.3` | Neutral or slight change |
| `< -0.1` | Negative or no reaction |

---

## 5. Training Design

### 5.1 Approach 1: Reward regression (LightGBM Regressor)

Predict reward directly for each pair of cat-state features and video-query features.

**Metrics**
- MAE for reward prediction error
- Spearman correlation for ranking quality across the 11 videos
- Top-1 Accuracy for whether the predicted best video matches the true best video

### 5.2 Approach 2: Learning to Rank (LightGBM Ranker)

Treat one session of one cat, consisting of 11 rows, as one group. Optimize ranking relationships instead of absolute reward values.

**Metrics**
- NDCG@1
- NDCG@3
- Top-1 Accuracy

### 5.3 Selection criteria

| Condition | Recommended approach |
|------|-------------|
| Small dataset (`< 100` sessions) | Prefer the regressor because the ranker may be unstable with too few groups |
| Sufficient dataset (`>= 100` sessions) | Prefer the ranker because relative ranking quality is stronger |
| Both are feasible | Compare on NDCG@1 and Top-1 Accuracy and adopt the better one |

**Initial policy:** start with Approach 1, then move to or compare with Approach 2 once enough data accumulates.

---

## 6. Validation Design

### Leave-one-cat-out cross-validation

This is the most suitable method for evaluating generalization under a small-data setting. Train on some cats and validate on a different cat to test whether the model works on unseen cats.

### Evaluation summary

| Metric | Unit | Target guide |
|------|---------|-------------|
| Top-1 Accuracy | Per session | `> 0.4` |
| Top-3 Accuracy | Per session | `> 0.7` |
| NDCG@1 | Per session | `> 0.6` |
| Spearman correlation | Per session | `> 0.3` |
| MAE | Regression only | Depends on data distribution |

---

## 7. Inference Flow

1. Receive the before image.
2. Extract three groups of features:
   - emotion probabilities
   - pose angles derived from ViTPose keypoints
   - CLIP prompt similarity scores
3. Concatenate those into the `before_vec`.
4. Score all 11 video queries by concatenating `before_vec` with each query embedding.
5. Return the best video ID and optionally top-3 IDs.
6. Pass the selected template and user context to Gemini.

### Output formats

| Output | Format | Purpose |
|------|------|------|
| `best_id` | `int` | Input to the Bandit layer and Gemini |
| `top3_ids` | `list[int]` | Used when multiple candidates are passed downstream |
| `scores` | `list[float]` | Used for Bandit updates or exploration logic |

---

## 8. JSON Data Structure and Pipeline Implementation

### 8.1 Training-data JSON

The session data stores:

- session ID
- cat ID
- video ID
- `before` features
- `after` features
- `reward`
- optional `human_label`

### 8.2 Feature-extraction pipeline

At startup, load:

- the emotion classifier
- ViTPose++
- CLIP model and processor

For each image:

1. predict emotion probabilities
2. extract keypoints and convert them into 12 pose-angle features
3. compute CLIP scores for the 8 prompts

### 8.3 Conversion to DataFrame

Convert the JSON structure into rows that contain:

- session-level metadata
- before-state features
- video-query embedding
- reward and label

so that LightGBM can train on a tabular representation.

---

## 9. ViTPose Keypoints -> Angle Features

Transform the 17 keypoints into hand-designed, more interpretable features such as:

- ear elevation angles
- asymmetry between both ears
- tail elevation
- spine curvature
- head tilt
- compactness of the body box
- activity score
- paw spread
- normalized nose height
- overall keypoint-confidence average

The intent is to compress raw coordinates into a stable feature set that better reflects interpretable cat posture.

---

## 10. CLIP Prompt Design

### Adopted prompt list

The prompt list is designed to represent interpretable cat states, including attentive, relaxed, stressed, playful, sleepy, alert, content, and bored.

### Prompt-selection policy

- use states that are easy for humans to interpret
- include both positive and negative states
- avoid overly fine-grained labels at the initial stage

---

## 11. TBD

- final PCA dimension for the query embeddings
- final reward-weight tuning
- final choice between regressor and ranker
- precise state-key generation logic
- validation thresholds after enough data is collected
