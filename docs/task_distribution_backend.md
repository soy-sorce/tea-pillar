# バックエンド役割分担（詳細版・初心者向け）

---

# 🎯 目的
- 誰がどのファイルを作るか明確にする
- 作業の待ち時間を減らす

---

# 🧱 全体構造（まずここを理解）

```
app.py（起動）
  ↓
routers（APIの入口）
  ↓
services（処理の中身）
  ↓
外部サービス（AI / Firestore）
```

👉 ルール
- routersはシンプルにする（受け取って渡すだけ）
- servicesに処理を書く

---

# 市岡担当

## 役割
「全体の流れをつなぐ人」

---

## 📁 担当ファイル

```
services/
 ├ orchestrator.py   ← 最重要
 ├ cat_model/client.py
 ├ gemini/client.py
 ├ veo/client.py
 ├ veo/signed_url.py
routers/
 └ generate.py
```

---

## 🧩 やること

### ① orchestrator.py

やること（順番通りに処理）：

1. セッション作成
2. Firestoreに保存
3. 猫AIを呼ぶ
4. state_key作成（Bさんの関数）
5. テンプレ選択（BさんのBandit）
6. Geminiで文章生成
7. Veoで動画生成
8. URL作成
9. Firestore更新

---

### ② routers/generate.py

- リクエストを受け取る
- orchestratorを呼ぶ
- 結果を返す

---

### ③ 外部サービス接続

#### cat_model/client.py
- 猫の状態を取得

#### gemini/client.py
- プロンプト生成

#### veo/client.py
- 動画生成

---

## ⚠️ 注意
- 最初はダミーでOK
- まずは一連の流れを動かす

---

# 古城担当

## 🎯 役割
「土台とシンプルな処理を作る人」

---

## 📁 担当ファイル

```
app.py
config.py
exceptions.py
logging_config.py

models/
 ├ request.py
 ├ response.py

routers/
 ├ feedback.py
 └ health.py

services/
 ├ firestore/client.py
 ├ bandit/base.py
 ├ bandit/ucb.py
 ├ state_key/builder.py
 └ gemini/prompt_builder.py

tests/
```

---

## 🧩 やること

### ① app.py
- FastAPIの起動
- router登録

---

### ② models/
- APIの入力・出力の形を定義

例：
```
class GenerateRequest:
    image_base64: str
    audio_base64: str
```

---

### ③ routers/feedback.py

やること：
1. reactionを受け取る
2. rewardに変換
3. Firestoreに保存
4. Bandit更新

---

### ④ routers/health.py

```
return {"status": "ok"}
```

---

### ⑤ firestore/client.py

- データ保存
- セッション更新
- フィードバック保存

---

### ⑥ state_key/builder.py

例：
```
happy_waiting_high
```

---

### ⑦ bandit/ucb.py

- テンプレ選択
- rewardで更新

---

### ⑧ prompt_builder.py

- Geminiに渡す文章を作る

---

### ⑨ テスト

対象：
- state_key
- reward変換
- bandit

---

# 🚀 開発の進め方

## Step1（最初）

- 古城：app.py / health
- 市岡：generate（ダミー）

---

## Step2

- 古城：state_key
- 市岡：orchestrator

---

## Step3

- 古城：bandit
- 市岡：gemini / veo

---

## Step4

- 古城：firestore
- 市岡：統合

---

