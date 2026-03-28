# 🐱 nekkoflix — 基本設計書

| 項目 | 内容 |
|------|------|
| ドキュメントバージョン | v3.0 |
| 作成日 | 2026-03-28 |
| ステータス | Active |
| 対応要件定義書 | docs/ja/Requirements_Definition.md |

---

## 目次

1. [システム構成図](#1-システム構成図)
2. [コンポーネント設計](#2-コンポーネント設計)
3. [処理フロー設計](#3-処理フロー設計)
4. [API設計（概要）](#4-api設計概要)
5. [画面設計](#5-画面設計)
6. [データ設計（論理）](#6-データ設計論理)
7. [インフラ設計](#7-インフラ設計)
8. [セキュリティ設計](#8-セキュリティ設計)
9. [エラー設計](#9-エラー設計)
10. [CI/CD設計](#10-cicd設計)
11. [非機能要件の具体化](#11-非機能要件の具体化)
12. [TBD（詳細設計フェーズへの持ち越し）](#12-tbd詳細設計フェーズへの持ち越し)

---

## 1. システム構成図

### 1.1 全体アーキテクチャ

```
┌──────────────────────────────────────────────────────────┐
│  ユーザーブラウザ（Chrome 最新版）                         │
│  Next.js / React (Cloud Run)                              │
└───────────────────────────┬──────────────────────────────┘
                            │ HTTPS
                            ▼
┌──────────────────────────────────────────────────────────┐
│  Cloud API Gateway                                        │
│  - JWT検証・レート制限・ルーティング                        │
│  - OpenAPI仕様による管理                                   │
└───────────────────────────┬──────────────────────────────┘
                            │ HTTPS（内部）
                            ▼
┌──────────────────────────────────────────────────────────┐
│  Backend API                                              │
│  Cloud Run  (Python / FastAPI)                            │
│  ingress: internal  /  min-instances: 1  /  timeout: 360s │
│                                                           │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  POST /generate                                          │ │
│  │  POST /sessions/{id}/reaction-upload-url                 │ │
│  │  POST /sessions/{id}/reaction                            │ │
│  │  GET  /health                                            │ │
│  │                                                          │ │
│  │  UCB Bandit ── インプロセス（探索・オンライン更新）    │ │
│  └─────────────────────────────────────────────────────────┘ │
└───┬──────────┬───────────┬──────────────┬────────────────┘
    │          │           │              │
    │ Direct   │ Vertex AI │ Vertex AI    │ Firestore
    │ VPC      │ API       │ API          │ API
    ▼          ▼           ▼              ▼
┌──────────┐ ┌───────┐ ┌──────────┐ ┌────────────────┐
│Vertex AI │ │Gemini │ │ Veo3.1   │ │ Cloud Firestore │
│Custom    │ │1.5    │ │ -fast on │ │                │
│Endpoint  │ │flash  │ │ Vertex AI│ │ sessions/      │
│          │ │       │ │          │ │ bandit_table/  │
│[猫4モデル│ │       │ │    │     │ │ templates/     │
│+LightGBM │ │       │ │    ▼     │ │ feedbacks/     │
│ Ranker統合│ │       │ │  GCS     │ └────────────────┘
└──────────┘ └───────┘ │  bucket  │
                       │  (一時)  │
                       └──────────┘
```

**設計方針サマリー：**

| 方針 | 内容 |
|---|---|
| 完全同期処理 | `POST /generate` は動画URLが返るまでHTTP接続を維持する |
| Cloud API Gateway | 認証（JWT検証）・レート制限・ルーティングの責務をBackendから分離 |
| GCS 一時利用 | Veo3がGCSへ書き込む仕様のため内部的に一時利用。Signed URLを発行してフロントへ渡す |
| Direct VPC | Backend → Vertex AI / Firestore / GCS の通信はVPC内で完結 |
| UCB Banditインプロセス | 探索ロジック（UCB）はBackend内で処理。Firestoreとの読み書きレイテンシを最小化 |
| 統合推論 Endpoint | `emotion / pose / clip / Reward Regressor` を同一Vertex AI Endpointに統合し、推論を1リクエストで完結させる |

### 1.2 リポジトリ構造

```
teapiller/
├── backend/                          # FastAPI (Cloud Run)
│   ├── src/app/
│   │   ├── main.py
│   │   ├── routers/
│   │   │   ├── generate.py
│   │   │   └── feedback.py
│   │   ├── services/
│   │   │   ├── cat_model.py          # Vertex AI Endpoint 呼び出し
│   │   │   ├── state_key.py          # 状態キー生成
│   │   │   ├── bandit/
│   │   │   │   ├── ucb.py            # UCBアルゴリズム
│   │   │   │   └── repository.py     # Firestore I/O
│   │   │   ├── gemini.py             # Gemini プロンプト再構築
│   │   │   ├── veo.py                # Veo3 生成 + GCS Signed URL
│   │   │   └── firestore.py          # Firestore ラッパー
│   │   └── models/
│   │       └── schemas.py            # Pydantic スキーマ
│   ├── tests/
│   ├── Dockerfile                    # Backend 専用
│   ├── pyproject.toml
│   └── .env.example
│
├── frontend/                         # Vite + React (Cloud Run)
│   ├── src/
│   │   ├── App.tsx                   # Router定義・GenerationContextProvider
│   │   ├── pages/
│   │   │   ├── LandingPage.tsx       # モード選択・コンセプト説明
│   │   │   ├── ExperiencePage.tsx    # 体験モード 3ステップ
│   │   │   ├── ProductionPage.tsx    # 本番モード 2ステップ
│   │   │   └── ResultPage.tsx        # 生成結果・reaction upload
│   │   ├── components/
│   │   │   ├── layout/               # AppLayout, StepIndicator
│   │   │   ├── result/               # VideoPlayer, LoadingScreen, ErrorScreen
│   │   │   └── ui/                   # Button, Toast, Spinner
│   │   ├── hooks/                    # useCamera, useMicrophone, useMotionDetection 等
│   │   ├── contexts/                 # GenerationContext
│   │   └── lib/                      # api.ts, audioUtils, imageUtils
│   ├── Dockerfile
│   ├── vite.config.ts
│   └── package.json
│
├── model/                            # Vertex AI Custom Endpoint
│   ├── src/
│   │   ├── predictor.py              # CPR エントリーポイント
│   │   ├── cat_meow.py
│   │   ├── cat_emotion.py
│   │   ├── vitpose.py
│   │   └── clip_scorer.py
│   ├── tests/
│   ├── Dockerfile                    # HuggingFace DLC ベース
│   └── requirements.txt
│
├── infra/
│   ├── terraform/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── cloud_run.tf
│   │   ├── vertex_ai.tf
│   │   ├── firestore.tf
│   │   └── gcs.tf
│   └── cloudbuild/
│       ├── cloudbuild-backend.yaml
│       ├── cloudbuild-frontend.yaml
│       └── cloudbuild-model.yaml
│
├── script/
│   ├── deploy_model_endpoint.py      # Vertex AI Endpoint 作成・登録
│   ├── init_firestore.py             # 初期テンプレートデータ投入
│   └── test_endpoint.py              # Endpoint 動作確認
│
├── docs/
│   ├── ja/                           # 日本語ドキュメント
│   │   ├── requirements_v1.md
│   │   ├── BasicDesign.md            # 本ドキュメント
│   │   ├── MODELING.md
│   │   └── modeling_plan.md
│   └── en/                           # 英語ドキュメント
│
├── docker-compose.yml                # ローカル開発用（frontend + backend のみ）
├── .env                              # ローカル用（gitignore 対象）
├── .env.example
├── .gitignore
└── README.md
```

> **補足：** `model/` は Vertex AI 上でのみ動作させる想定のため `docker-compose.yml` には含めない。ローカル動作確認は `script/test_endpoint.py` でデプロイ済み Endpoint を叩く。

---

## 2. コンポーネント設計

### 2.1 Frontend（Cloud Run / Next.js）

**責務：**
- 画面描画・ルーティング（React Router v7）
- ユーザー入力の受付（カメラ・マイク・コンテキストテキスト）
- `diff-cam-engine` による動き検知・自動キャプチャ
- Backend への HTTP リクエスト発行
- ローディング・ステップ進捗表示
- 動画再生（Signed URL を `<video>` タグで再生）
- 本番モード時の reaction video 録画・GCS upload・backend 通知

**スタックと主要設定：**

| 項目 | 選定・設定値 |
|---|---|
| フレームワーク | Vite + React 19 |
| ルーティング | React Router v7（`react-router-dom`）|
| 言語 | TypeScript |
| スタイリング | Tailwind CSS + カスタムCSS |
| デプロイ形態 | Cloud Run（Dockerコンテナ） |
| 動き検知 | `diff-cam-engine`（フレーム差分方式） |
| 録音・録画 | `MediaRecorder` Web API |
| リクエストタイムアウト | 360秒（Veo3生成を考慮） |

---

### 2.2 Cloud API Gateway

**責務：**
- JWT検証（IDトークンの有効性確認）
- レート制限（デモ中の過剰リクエスト防止）
- ルーティング（`/generate`・`/feedback`・`/health` → Backend Cloud Run）
- APIのOpenAPI仕様による管理

**スタックと主要設定：**

| 項目 | 選定・設定値 |
|---|---|
| サービス | Cloud API Gateway |
| 設定ファイル | `infra/apigateway/openapi.yaml`（OpenAPI 2.0形式） |
| バックエンド | Backend Cloud Run の内部URL |
| 認証 | Google IDトークン検証（`securityDefinitions` で設定） |
| BackendのIngress変更 | `internal`（API Gatewayからのみ受け付け） |

---

### 2.3 Backend API（Cloud Run / FastAPI）

**責務：**
- セッション管理（session_id 生成・Firestore への状態書き込み）
- Vertex AI 猫モデル Endpoint 呼び出し
- 状態キー生成（4モデル出力を結合）
- Bandit によるテンプレート選択（インプロセス UCB）
- Gemini へのプロンプト再構築リクエスト
- Veo3 への動画生成リクエスト・GCS Signed URL 取得
- フロントへの動画 URL 返却
- フィードバック受信・報酬計算・Banditテーブル更新

**スタックと主要設定：**

| 項目 | 選定・設定値 |
|---|---|
| フレームワーク | FastAPI |
| 言語 | Python 3.11 |
| デプロイ形態 | Cloud Run（Dockerコンテナ） |
| Cloud Run タイムアウト | 360秒 |
| Cloud Run min-instances | 1（コールドスタート防止） |
| Cloud Run ingress | `internal`（API Gatewayからのみ受け付け） |
| 主要ライブラリ | `google-cloud-aiplatform`、`google-cloud-firestore`、`google-cloud-storage` |

---

### 2.4 Vertex AI 猫モデル + LightGBM Ranker Endpoint（統合）

猫分析4モデルとLightGBM Rankerを1つのカスタムコンテナに統合し、1 Endpoint として公開する。

| 項目 | 選定・設定値 |
|---|---|
| デプロイ方式 | Vertex AI Custom Prediction Routine（CPR） |
| ベースイメージ | `huggingface-pytorch-inference-cu121`（HuggingFace 公式 DLC） |
| 初期インスタンスタイプ | `n1-standard-4`（CPU）→ 性能不足時は GPU（T4）へ移行 |
| min-replica-count | 1（デモ当日のコールドスタート防止） |

**統合されるモデル：**

| モデル | 役割 | 出力 |
|---|---|---|
| `IsolaHGVIS/Cat-Meow-Classification` | 鳴き声分類 | `brushing` / `waiting_for_food` / `isolation` |
| `semihdervis/cat-emotion-classifier` | 顔感情分類 | `happy` / `sad` / `angry` |
| `usyd-community/vitpose-plus-plus-small`（AP-10K head） | 全身ポーズ推定 | キーポイント17点 × (x, y, conf) + 角度特徴量12次元 |
| `openai/clip-vit-base-patch32` | 状態ゼロショット分類 | カスタムプロンプト8種との類似度スコア |
| LightGBM Ranker（学習済み） | テンプレートスコアリング | 全11テンプレートの予測報酬スコア（11次元） |

**LightGBM Rankerの役割と入力：**
- 入力：猫状態特徴量（emotion 3次元 + pose_angles 12次元 + clip_scores 8次元）× 動画クエリembedding（PCA 16次元）= 39次元
- 出力：全11テンプレートに対するスコア配列
- Endpoint統合の意図：猫モデルの出力を即座にRankerに渡せるため、Backend往復が不要でレイテンシを削減できる

---

### 2.5 Bandit（Backend インプロセス / UCB 探索ロジック）

**役割：** LightGBM Rankerが算出した各テンプレートの予測スコアをベースに、UCBの探索ボーナスを加算して最終的な選択テンプレートを決定する。

**LightGBM RankerとUCBの役割分担：**

| コンポーネント | 役割 | 配置 |
|---|---|---|
| LightGBM Ranker | 猫の状態から各テンプレートの予測報酬スコアを算出（exploitation） | Vertex AI Endpoint |
| UCB Bandit | RankerスコアにUCB探索ボーナスを加算し、未試行テンプレートの探索を保証（exploration） | Backend インプロセス |

**UCB1 探索ボーナス計算：**

```
final_score(i) = ranker_score(i) + α × √(2 × ln(N) / n(i))

ranker_score(i): LightGBM Rankerが出力した予測スコア
α              : 探索の重みパラメータ（デフォルト1.0）
N              : 全テンプレートの累積選択回数
n(i)           : テンプレート i の選択回数（Firestoreから取得）
```

**拡張性：** `bandit/ucb.py` は `BanditBase` 抽象クラスを実装する形にし、将来的なアルゴリズム差し替えをインターフェース変更なしで行えるようにする。

---

### 2.6 Gemini（gemini-1.5-flash）

**役割：** テンプレートプロンプト＋状態キー＋ユーザーコンテキストを受け取り、Veo3向けの動画生成プロンプトを再構築して出力する。

**Backend が組み立てる Gemini への prompt 構造（概要）：**

```
[SYSTEM]
あなたは猫向け動画のプロンプトクリエイターです。
以下の情報を元に、Veo3で生成する動画のプロンプトを1件出力してください。
出力はプロンプト文字列のみ（説明文・前置き不要）。

[テンプレート]
{selected_template_text}

[猫の現在の状態]
感情: {emotion_label}
鳴き声: {meow_label}
注目スコア: {clip_attentive:.2f}
活発度: {pose_activity:.2f}

[オーナーが設定した猫の性格・好み]
{user_context}

[制約]
- 動画は音声なし
- 猫が興味を持ちやすい動きのある映像
- 10〜15秒程度の短編
```

---

### 2.7 Veo3（veo-3.1-fast on Vertex AI）

**役割：** Gemini が生成したプロンプトを受け取り、mp4動画を生成してGCSへ書き込む。

| 項目 | 内容 |
|---|---|
| モデル | `veo-3.1-fast` |
| 生成オプション | 音声なし（`generate_audio: false`） |
| 出力先 | GCS バケット（Backend が Signed URL を発行してフロントへ渡す） |
| 想定生成時間 | 30秒〜180秒 |
| Signed URL 有効期限 | 1時間 |

**GCS との関係：** Veo3 on Vertex AI は内部仕様として生成動画を GCS へ書き込む。Backend は生成完了後に GCS オブジェクトの Signed URL を発行し、フロントへ返す。GCS バケットはユーザーに非公開。動画ファイルはライフサイクルポリシーにより1日後に自動削除。

---

## 3. 処理フロー設計

### 3.1 POST /generate の処理フロー（主系）

```
Frontend        API Gateway       Backend (FastAPI)          外部サービス
   │                │                   │
   │ POST /generate │                   │
   │ ──────────────►│                   │
   │                │ JWT検証・ルーティング│
   │                │ ──────────────────►│
   │                │                   │ 1. session_id 生成 (UUID v4)
   │                │                   │ 2. Firestore: status=generating
   │                │                   │
   │                │                   │ 3. Vertex AI Endpoint へ推論リクエスト
   │                │                   │ ───────────────────────────────► Vertex AI
   │                │                   │    [猫モデル4本 → 特徴量抽出]
   │                │                   │    [LightGBM Ranker → テンプレートスコア11次元]
   │                │                   │ ◄─────────────── features + ranker_scores[11]
   │                │                   │
   │                │                   │ 4. 状態キー生成
   │                │                   │ 5. UCB探索ボーナス加算
   │                │                   │    final_score = ranker_score + α√(2lnN/n)
   │                │                   │    → template_id 選択
   │                │                   │
   │                │                   │ 6. Gemini: プロンプト再構築
   │                │                   │ ───────────────────────────────► Gemini
   │                │                   │ ◄──────────────────── 生成プロンプト文字列
   │                │                   │
   │                │                   │ 7. Veo3: 動画生成リクエスト
   │                │                   │ ───────────────────────────────► Veo3
   │                │                   │    （ポーリングで完了を待機）
   │                │                   │ ◄────────────────── GCS オブジェクト URI
   │                │                   │
   │                │                   │ 8. GCS Signed URL 生成（有効期限 1時間）
   │                │                   │ 9. Firestore: status=done 更新
   │                │                   │
   │ 200 OK         │                   │
   │ ◄──────────────────────────────────│
   │ { video_url, session_id,           │
   │   state_key, template_id }         │
```

### 3.2 本番モード reaction video アップロードフロー

```
Frontend（ResultPage）          Backend (FastAPI)          GCS
   │                                │
   │  動画再生開始（onPlay）         │
   │  → reaction camera 起動        │
   │  → useReactionRecorder.start() │
   │    （最大8秒録画）              │
   │                                │
   │  POST /sessions/{id}/          │
   │  reaction-upload-url           │
   │ ──────────────────────────────►│
   │                                │ GCS Signed URL 発行
   │ ◄──────────────────────────── │
   │  { upload_url,                 │
   │    reaction_video_gcs_uri }    │
   │                                │
   │  PUT upload_url (Blob)         │
   │ ──────────────────────────────────────────────► GCS
   │ ◄────────────────────────────────────────────── 200 OK
   │                                │
   │  POST /sessions/{id}/reaction  │
   │  { reaction_video_gcs_uri }    │
   │ ──────────────────────────────►│
   │                                │ Banditテーブル更新（非同期）
   │  200 OK { status: accepted }   │
   │ ◄──────────────────────────── │
```

> **体験モードでは上記フローは走らない。** ResultPage は `input.mode === "production"` のときのみ reaction camera を起動する。

---

## 4. API設計（概要）

### 4.1 エンドポイント一覧

| メソッド | パス | 概要 | 認証 |
|---|---|---|---|
| `GET` | `/health` | ヘルスチェック | 不要 |
| `POST` | `/generate` | メイン生成フロー | IDトークン必須 |
| `POST` | `/sessions/{session_id}/reaction-upload-url` | reaction video 用 GCS signed URL 発行 | IDトークン必須 |
| `PUT` | `<GCS signed URL>` | reaction video を GCS へ直接アップロード | 不要（GCS） |
| `POST` | `/sessions/{session_id}/reaction` | reaction video URI 通知・Bandit 更新 | IDトークン必須 |

### 4.2 POST /generate

**リクエストボディ：**

| フィールド | 型 | 必須 | 説明 |
|---|---|---|---|
| `mode` | string | ✅ | `experience` または `production` |
| `image_base64` | string | ✅ | Base64エンコードされた猫の画像（JPEG/PNG） |
| `audio_base64` | string | ❌ | Base64エンコードされたWAV音声。未指定時は音声なしとして処理 |
| `user_context` | string | ❌ | 猫の性格・好みの文字列。空の場合はデフォルト（指定なし） |

**レスポンス（200 OK）：**

| フィールド | 型 | 説明 |
|---|---|---|
| `session_id` | string | UUID v4 |
| `video_url` | string | GCS Signed URL（有効期限1時間） |
| `state_key` | string | 生成された状態キー（例: `waiting_for_food_happy_attentive`） |
| `template_id` | string | Banditが選択したテンプレートID（例: `T02`） |
| `template_name` | string | テンプレート名（例: `playful yarn ball bouncing`） |

**エラーレスポンス：**

| フィールド | 型 | 説明 |
|---|---|---|
| `error_code` | string | `VERTEX_TIMEOUT` / `VEO_FAILED` / `INVALID_INPUT` / `INTERNAL_ERROR` 等 |
| `message` | string | エラーの説明 |
| `session_id` | string | セッションID（生成済みの場合） |

### 4.3 POST /sessions/{session_id}/reaction-upload-url

**レスポンス（200 OK）：**

| フィールド | 型 | 説明 |
|---|---|---|
| `session_id` | string | セッションID |
| `upload_url` | string | GCS signed PUT URL（有効期限あり） |
| `reaction_video_gcs_uri` | string | GCS 上の reaction video の保存先 URI |
| `expires_in_seconds` | number | signed URL の有効秒数 |

### 4.4 POST /sessions/{session_id}/reaction

**リクエストボディ：**

| フィールド | 型 | 必須 | 説明 |
|---|---|---|---|
| `reaction_video_gcs_uri` | string | ✅ | GCS 上の reaction video の URI |

**レスポンス（200 OK）：**

| フィールド | 型 | 説明 |
|---|---|---|
| `status` | string | `accepted` |

### 4.5 GET /health

**レスポンス（200 OK）：**

| フィールド | 型 | 説明 |
|---|---|---|
| `status` | string | `ok` |
| `timestamp` | string | ISO 8601形式の現在時刻 |

---

## 5. 画面設計

### 5.1 画面一覧

| 画面ID | 画面名 | パス | 概要 |
|---|---|---|---|
| P-01 | ランディング（モード選択） | `/` | 体験モード / 本番モードの選択・コンセプト説明 |
| P-02 | 体験モード | `/experience` | 3ステップ（撮影・鳴きマネ録音・コンテキスト入力） |
| P-03 | 本番モード | `/production` | 2ステップ（コンテキスト入力・撮影/録音） |
| P-04 | 生成中ローディング | `/result`（loading） | ローディングアニメーション |
| P-05 | 動画再生・結果 | `/result`（done） | 体験：ループ再生＋生成情報 / 本番：reaction camera付き |
| P-06 | エラー画面 | `/result`（error） | エラーメッセージ＋リトライボタン |

### 5.2 画面遷移図

```
[P-01 ランディング]
    │
    ├── 体験モードで試す ──► [P-02 体験モード /experience]
    │                            │
    │                            │ Step 1: カメラ起動 → 動き検知 → 自動キャプチャ
    │                            │ Step 2: 「録音を開始する（3秒）」ボタン → 自動遷移
    │                            │ Step 3: コンテキスト入力 → 「動画を生成する」
    │                            │
    └── 本番モードで使う ──► [P-03 本番モード /production]
                                 │
                                 │ Step 1: コンテキスト入力 → 「次へ」
                                 │ Step 2: カメラ起動 → 動き検知 → 自動撮影・録音 → 自動送信
    ◄────────────────────────────┘
    │ POST /generate
    ▼
[P-04 生成中ローディング /result]
    │
    ├── 200 OK ──► [P-05 動画再生・結果]
    │                 │
    │                 │ 体験モード: VideoPlayer（ループ）+ 生成情報
    │                 │ 本番モード: VideoPlayer + reaction camera + upload状態
    │                 │
    │                 └── もう一度試す ──► [P-01]
    │
    └── エラー ──────► [P-06 エラー画面]
                            │
                            ├── リトライ ──► [P-04]（navigate(0)）
                            └── 戻る ────► [P-02/P-03]（navigate(-1)）
```

### 5.3 各画面の主要要素（概要）

**P-01 ランディング**
- nekkoflixロゴ・キャッチコピー
- コンセプト説明カード（Pets in the Loop）
- 「体験モードで試す」カード → `/experience`
- 「本番モードで使う」カード → `/production`

**P-02 体験モード（`/experience`）**
- StepIndicator（3ステップ）
- Step 1: カメラプレビュー + 動き検知ステータス（自動キャプチャ待ち）
- Step 2: マイクアイコン + 「録音を開始する（3秒）」ボタン → カウントダウン
- Step 3: コンテキストテキストエリア（任意）+ 「動画を生成する」ボタン

**P-03 本番モード（`/production`）**
- StepIndicator（2ステップ）
- Step 1: コンテキストテキストエリア（任意）+ 「次へ」ボタン
- Step 2: カメラプレビュー + 動き検知ステータス（自動キャプチャ・録音・送信）

**P-04 生成中ローディング**
- ローディングアニメーション
- ステップメッセージサイクル（Geminiプロンプト生成中 → Veo3動画生成中）
- 「通常30秒〜3分かかります」目安表示

**P-05 動画再生・結果**
- 体験モード: VideoPlayer（ループ再生）+ テンプレート名/state_keyカード + 「もう一度試す」
- 本番モード: VideoPlayer（1回再生）+ reaction camera プレビュー + upload状態バッジ + 「もう一度試す」

**P-06 エラー画面**
- エラーメッセージ
- リトライボタン / トップへ戻るボタン

---

## 6. データ設計（論理）

### 6.1 Firestore コレクション構造

```
firestore/
├── sessions/       {session_id}     # UUID v4
├── bandit_table/   {template_id}    # 例: T01〜T50
├── templates/      {template_id}    # 例: T01〜T50
└── feedbacks/      {feedback_id}    # UUID v4
```

### 6.2 sessions コレクション

| フィールド名 | 型 | 必須 | 説明 |
|---|---|---|---|
| `session_id` | string | ✅ | UUID v4 |
| `mode` | string | ✅ | `experience` \| `production` |
| `status` | string | ✅ | `generating` \| `done` \| `failed` |
| `state_key` | string | ❌ | 生成された状態キー |
| `template_id` | string | ❌ | Banditが選択したテンプレートID |
| `user_context` | string | ❌ | オーナーが入力したコンテキスト |
| `video_gcs_uri` | string | ❌ | GCSの動画URI（内部管理用） |
| `error` | string | ❌ | エラー時のメッセージ |
| `created_at` | timestamp | ✅ | セッション作成日時 |
| `completed_at` | timestamp | ❌ | 生成完了日時 |

### 6.3 bandit_table コレクション

UCBアルゴリズムが参照・更新するテーブル。

| フィールド名 | 型 | 必須 | 説明 |
|---|---|---|---|
| `template_id` | string | ✅ | テンプレートID |
| `state_key` | string | ✅ | 猫の状態キー |
| `selection_count` | number | ✅ | 選択回数 |
| `cumulative_reward` | number | ✅ | 累積報酬 |
| `mean_reward` | number | ✅ | 平均報酬（= cumulative / count） |
| `updated_at` | timestamp | ✅ | 最終更新日時 |

> **初期値：** `script/init_firestore.py` で全テンプレート × 全状態キーの組み合わせに `selection_count=1`、`cumulative_reward=0`、`mean_reward=0` を投入し、コールドスタートを防ぐ。

### 6.4 templates コレクション

| フィールド名 | 型 | 必須 | 説明 |
|---|---|---|---|
| `template_id` | string | ✅ | テンプレートID（例: `T02`） |
| `name` | string | ✅ | テンプレート名 |
| `prompt_text` | string | ✅ | Geminiに渡すプロンプトのひな形 |
| `clip_embedding` | array[float] | ❌ | CLIPテキストembedding PCA16次元（将来のLightGBM Rankerで使用） |
| `is_active` | boolean | ✅ | 有効フラグ（falseはBandit選択対象外） |
| `auto_generated` | boolean | ✅ | Geminiによる自律生成かどうか |
| `created_at` | timestamp | ✅ | 作成日時 |

### 6.5 feedbacks コレクション

| フィールド名 | 型 | 必須 | 説明 |
|---|---|---|---|
| `session_id` | string | ✅ | 対応するセッションID |
| `template_id` | string | ✅ | 対象テンプレートID |
| `reaction_video_gcs_uri` | string | ✅ | GCS 上の reaction video の URI |
| `reward` | number | ✅ | reaction video 解析による報酬値 |
| `created_at` | timestamp | ✅ | 記録日時 |

### 6.6 報酬値の設計

体験モードではフィードバック・報酬計算は行わない。本番モードのみ。

| 方式 | 内容 |
|---|---|
| reaction video | 動画再生中に最大8秒間録画した猫の反応映像 |
| 報酬計算 | Backend が reaction video を解析して reward を算出（AI自動評価）|
| 旧方式（廃止） | 人間が 😺/😐/😾 を選択する `/feedback` ボタン方式は廃止 |

---

## 7. インフラ設計

### 7.1 GCPリソース一覧

| リソース名 | サービス | 主要設定値 | 役割 |
|---|---|---|---|
| `nekkoflix-frontend` | Cloud Run | min=0, max=3, timeout=60s | フロントエンド配信 |
| `nekkoflix-api-gateway` | Cloud API Gateway | OpenAPI 2.0定義 | JWT検証・ルーティング・レート制限 |
| `nekkoflix-backend` | Cloud Run | min=1, max=5, timeout=360s, ingress=internal | バックエンドAPI |
| `nekkoflix-cat-model` | Vertex AI Endpoint | min-replica=1, n1-standard-4（CPU） | 猫4モデル + LightGBM Ranker統合推論 |
| `nekkoflix-firestore` | Cloud Firestore | Native mode, asia-northeast1 | データ永続化 |
| `nekkoflix-videos` | Cloud Storage | asia-northeast1, ライフサイクル1日後削除 | Veo3生成動画の一時保存 |

### 7.2 ネットワーク設計

```
Internet
   │
   ▼
[Cloud Run frontend]      ingress: all（パブリック公開）
   │ IDトークン付与
   ▼
[Cloud API Gateway]       JWT検証・レート制限・ルーティング
   │
   ▼
[Cloud Run backend]       ingress: internal（API Gatewayからのみ）
   │
   │ Direct VPC Egress
   ├──► Vertex AI API（猫モデル+Ranker Endpoint・Gemini・Veo3）
   ├──► Cloud Firestore API
   └──► Cloud Storage API
```

- Frontend → API Gateway：IDトークン付与
- API Gateway → Backend：JWT検証済みリクエストを内部転送
- Backend → GCPサービス：サービスアカウント + ADC経由
- ALBは使用しない

### 7.3 IAM設計

| サービスアカウント | 付与するロール | 用途 |
|---|---|---|
| `nekkoflix-frontend-sa` | `roles/serviceusage.serviceUsageConsumer` | IDトークン取得 |
| `nekkoflix-apigateway-sa` | `roles/run.invoker`（backend対象） | API GatewayからBackend Cloud Runの呼び出し権限 |
| `nekkoflix-backend-sa` | `roles/aiplatform.user` | Vertex AI / Gemini / Veo3 呼び出し |
| `nekkoflix-backend-sa` | `roles/datastore.user` | Firestore 読み書き |
| `nekkoflix-backend-sa` | `roles/storage.objectAdmin` | GCS 読み書き・Signed URL発行 |

### 7.4 環境変数設計（`.env.example`）

```bash
# GCP
GCP_PROJECT_ID=REPLACE_ME_PROJECT_ID
GCP_REGION=asia-northeast1

# Vertex AI
VERTEX_CAT_MODEL_ENDPOINT_ID=your-endpoint-id
VERTEX_CAT_MODEL_ENDPOINT_LOCATION=asia-northeast1

# Gemini
GEMINI_MODEL=gemini-1.5-flash

# Veo3
VEO_MODEL=veo-3.1-fast

# GCS
GCS_BUCKET_NAME=nekkoflix-videos
GCS_SIGNED_URL_EXPIRATION_HOURS=1

# Firestore
FIRESTORE_DATABASE_ID=(default)

# Frontend → Backend URL
NEXT_PUBLIC_BACKEND_URL=https://nekkoflix-backend-xxxx-an.a.run.app

# 実行環境
ENVIRONMENT=development
```

### 7.5 GCS ライフサイクルポリシー

```json
{
  "rule": [
    {
      "action": { "type": "Delete" },
      "condition": { "age": 1 }
    }
  ]
}
```

> 動画オブジェクト作成から1日後に自動削除。Signed URL（有効1時間）内に再生が完了する設計のため問題ない。

---

## 8. セキュリティ設計

### 8.1 認証・認可方式

| 通信経路 | 方式 | 詳細 |
|---|---|---|
| ブラウザ → Frontend | オープンアクセス | 認証なし（ハッカソンデモのため） |
| Frontend → API Gateway | IDトークン（Bearer） | FrontendのSAが取得したIDトークンをAuthorizationヘッダーに付与 |
| API Gateway → Backend | JWT検証済みの内部転送 | API GatewayがJWT検証後、BackendのCloud Run内部URLへ転送 |
| Backend → GCPサービス | サービスアカウント + ADC | Cloud Run上では自動的にSAを使用 |

### 8.2 シークレット管理

| シークレット | 管理方法 |
|---|---|
| GCPサービスアカウントキー | 使用しない（Cloud Run 上では ADC を使用） |
| 環境変数 | Cloud Run の環境変数として設定。`.env` はローカル開発用のみ（gitignore対象） |
| APIキー類 | すべてバックエンドサイドで管理。フロントエンドへは一切露出しない |

### 8.3 入力ファイルの取り扱い

- アップロードされた画像・音声はメモリ上で処理し、ディスクへ永続化しない
- Vertex AI Endpoint へはBase64エンコードしてリクエストボディに含めて送信
- Backend の Cloud Run コンテナはステートレス設計

---

## 9. エラー設計

### 9.1 エラー種別と対応

| エラーコード | 発生箇所 | HTTP | ユーザー向け表示 | Firestore |
|---|---|---|---|---|
| `INVALID_INPUT` | Backend バリデーション | 400 | 「入力データに問題があります」 | status=failed |
| `VERTEX_TIMEOUT` | Vertex AI 推論 | 504 | 「解析に時間がかかっています。もう一度お試しください」 | status=failed（リトライ可） |
| `GEMINI_FAILED` | Gemini プロンプト生成 | 502 | 「プロンプトの生成に失敗しました」 | status=failed |
| `VEO_FAILED` | Veo3 動画生成 | 502 | 「動画の生成に失敗しました。もう一度お試しください」 | status=failed（リトライ可） |
| `VEO_TIMEOUT` | Veo3 タイムアウト | 504 | 「動画生成がタイムアウトしました」 | status=failed |
| `INTERNAL_ERROR` | Backend 予期しないエラー | 500 | 「予期しないエラーが発生しました」 | status=failed・ログ出力 |

### 9.2 タイムアウト設計

| 処理 | タイムアウト値 | 根拠 |
|---|---|---|
| Cloud Run Backend | 360秒 | Veo3最大想定（180秒）＋バッファ |
| Frontend fetch | 360秒 | Backend に揃える |
| Vertex AI 猫モデル推論 | 30秒 | 4モデル直列実行の想定上限 |
| Gemini プロンプト生成 | 15秒 | 軽量リクエストのため余裕を持たせる |
| Veo3 動画生成 | 300秒 | Veo3の生成時間の想定上限 |
| Firestore 読み書き | 10秒 | 通常1秒未満 |

### 9.3 フォールバック設計（体験モード）

```
入力方法B（マイク/カメラ）
    │
    ├── MediaDevices API 非対応 ──► 即時フォールバック
    ├── 録音・撮影失敗 ──────────► 即時フォールバック
    └── 解析エラー（非200応答） ──► 即時フォールバック
                │
                ▼
        トースト通知表示（3秒）
        「カメラ/マイクが使用できませんでした。サンプル選択に切り替えます」
                │
                ▼
        入力方法A（サンプル選択）へ自動遷移
```

---

## 10. CI/CD設計

### 10.1 Cloud Build トリガー

| トリガー名 | 発火条件 | 対象 | 設定ファイル |
|---|---|---|---|
| `build-backend` | `main` push（`backend/**` 変更時） | Backend Cloud Run | `infra/cloudbuild/cloudbuild-backend.yaml` |
| `build-frontend` | `main` push（`frontend/**` 変更時） | Frontend Cloud Run | `infra/cloudbuild/cloudbuild-frontend.yaml` |
| `build-model` | 手動トリガー or `model/**` 変更時 | Vertex AI Custom Container | `infra/cloudbuild/cloudbuild-model.yaml` |

> モデルコンテナの更新頻度は低いため、手動トリガーを基本とする。

### 10.2 デプロイフロー（Backend / Frontend）

```
git push main
    │
    ▼
Cloud Build トリガー起動
    │
    ├── 1. docker build（各 Dockerfile を使用）
    ├── 2. docker push（Artifact Registry へ）
    └── 3. Cloud Run deploy（新リビジョンへトラフィック切り替え）
```

### 10.3 モデル Endpoint デプロイフロー

```
手動実行: python script/deploy_model_endpoint.py
    │
    ├── 1. model/ のイメージをビルド（Cloud Build 経由）
    ├── 2. Artifact Registry へ push
    ├── 3. Vertex AI Model Registry へモデル登録
    └── 4. Vertex AI Endpoint へデプロイ（min-replica=1）
```

---

## 11. 非機能要件の具体化

### 11.1 性能

| 要件定義の目標 | 本設計での具体値 |
|---|---|
| 猫状態解析：10秒以内 | Vertex AI Endpoint タイムアウト30秒。CPU n1-standard-4 で性能不足時はGPU（T4）へ移行 |
| Geminiプロンプト生成：数秒以内 | タイムアウト15秒 |
| Veo3動画生成：SLAなし | タイムアウト300秒。生成中はローディング表示。「通常30秒〜3分」を画面に表示 |
| Backend全体 | Cloud Run タイムアウト360秒 |

### 11.2 可用性

| 要件定義の目標 | 本設計での具体値 |
|---|---|
| ハッカソン当日の継続稼働 | Backend min-instances=1。Vertex AI min-replica=1（コールドスタートなし） |
| フォールバックによるデモ継続 | 体験モードB→A自動切り替え（セクション9.3） |
| Veo3失敗時のリカバリ | エラー画面にリトライボタン。同一リクエストで `/generate` を再呼び出し |

### 11.3 拡張性（審査員へのアピールポイント）

| 現在のMVP設計 | 将来の拡張シナリオ |
|---|---|
| UCB Banditインプロセス | `BanditBase` 抽象クラス経由でアルゴリズム差し替え可能 |
| LightGBM Ranker統合Endpoint | 独立Endpointへの分離・モデル更新の独立化が可能 |
| Cloud API Gateway | Apigeeへの移行でより高度なAPIマネジメント（分析・課金・バージョン管理）が可能 |
| GCS Signed URLで動画渡し | CDN経由配信へ移行容易 |
| 猫のみ対応 | ViTPose++ AP-10K headで犬・うさぎ等46種に対応可能 |
| HuggingFaceモデル固定 | Vertex AI Model Registry 経由でバージョン管理・差し替え可能 |

---

## 12. TBD（詳細設計フェーズへの持ち越し）

| # | 項目 | 内容 | 担当設計書 |
|---|---|---|---|
| TBD-1 | 状態キー生成ロジック | ✅ **解決済み** — emotion/meow/clip/pose 結合キー実装済み | Backend詳細設計 |
| TBD-2 | Bandit UCBパラメータ | ✅ **解決済み** — UCB1、α=1.0 で実装。調整は運用フェーズへ | Backend詳細設計 |
| TBD-3 | 体験モードBのViTPose++/CLIP処理 | ✅ **解決済み** — 体験モードのサンプル選択廃止。全モードでカメラ画像から直接推論 | — |
| TBD-4 | Vertex AI インスタンス移行基準 | ✅ **解決済み** — CPU `n1-standard-4` で稼働。GPU移行判断は運用フェーズ | インフラ詳細設計 |
| TBD-5 | GeminiプロンプトのFew-shot例 | 🔲 **継続TBD** — 品質は運用データで改善。Few-shot設計は継続検討 | Backend詳細設計 |
| TBD-6 | Firestore セキュリティルール | 🔲 **継続TBD** — MVP はハッカソンのため簡易設定。本番前に要対応 | インフラ詳細設計 |
| TBD-7 | ローカル開発時のモックAPI | 🔲 **継続TBD** — 現状は実Endpointを使用。モック設計は継続検討 | Backend詳細設計 |
| TBD-8 | テンプレート進化（Layer 6）の実装方針 | 🔲 **継続TBD** — Gemini自律生成は未実装。将来の拡張項目 | Backend詳細設計 |
| TBD-9 | フロントエンドコンポーネント詳細 | ✅ **解決済み** — `docs/ja/Fronted_Desgin.md`（フロントエンド詳細設計書）に文書化済み | フロントエンド詳細設計 |
| TBD-10 | Veo3 ポーリング vs Webhook | 🔲 **継続TBD** — 現状ポーリング方式。Webhookサポート確認後に判断 | Backend詳細設計 |
