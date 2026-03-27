# フロントUI設計とAPI仕様整理

最終更新: 2026-03-21
対象実装:
- `frontend/`
- `backend/src/routers/`
- `backend/src/models/`

## 1. この資料の目的

今後の改善対象を「通信を伴わないUI」に限定するため、現行フロントの画面設計とAPI契約をコード基準で整理する。

この資料では次を明確化する。
- どの画面、コンポーネント、状態が存在するか
- どこでAPIを呼んでいるか
- 今後変更してよいUI要素と、変更しないべき通信仕様

## 2. 現行アーキテクチャ要約

- フロントは React 19 + Vite + TypeScript + Tailwind CSS
- ルーティングは `react-router-dom@7`
- 画面状態は `GenerationContext` で共有
- API呼び出しは `frontend/src/lib/api.ts` の `post()` に集約
- フロントから使っているAPIは `POST /generate` と `POST /feedback` の2本のみ

## 3. 画面構成

### 3.1 ルーティング

- `/`
  - 実質的なメイン画面
  - トップヒーロー、フロー説明、モード切替タブ、入力フォームを内包
- `/result`
  - 生成中、生成結果、エラーの3状態を切り替えて表示
- `/experience`
  - 現在は `/` へ `redirect`
- `/production`
  - 現在は `/` へ `redirect`

補足:
- 旧設計書は体験モード・本番モードを別ページ前提で書かれているが、現実装は「トップ画面内タブ切替」である

### 3.2 画面の実体

#### トップ画面 `/`

`frontend/src/pages/TopPage.tsx`

構成:
- ヒーロー領域
- `FlowDiagram`
- モード切替タブ
  - `experience`
  - `production`
- タブに応じて下記フォームを出し分け
  - `ExperienceForm`
  - `ProductionForm`

特徴:
- 初回表示時に `GenerationContext.reset()` を実行
- タブ切替時にも `reset()` を実行

#### 結果画面 `/result`

`frontend/src/pages/ResultPage.tsx`

`GenerationContext.resultState` により表示分岐:
- `loading`
  - `LoadingScreen`
- `done`
  - `VideoPlayer`
  - `FeedbackButtons`
  - 再試行ボタン
- `error`
  - `ErrorScreen`
- `idle`
  - `/` へ戻す

## 4. フォーム別UI設計

### 4.1 体験モード

`frontend/src/components/forms/ExperienceForm.tsx`

入力要素:
- Step 1: 鳴き声
  - サンプル選択
  - またはマイク録音
- Step 2: 写真
  - サンプル画像選択
- Step 3: 性格・文脈
  - 任意テキスト入力

送信条件:
- 音声があること
  - 録音済み、または鳴き声サンプル選択済み
- 画像があること
  - 写真サンプル選択済み

実装上の注意:
- 鳴き声サンプルを選んでも、現時点では `audio_base64` は送っていない
- コメントにある通り、`/samples/audio/*.wav` が未配備のため暫定的に無音で送信される実装
- つまり体験モードで確実に音声が載るのは「マイク録音」の場合のみ

### 4.2 本番モード

`frontend/src/components/forms/ProductionForm.tsx`

入力要素:
- 鳴き声ファイルアップロード
  - 任意
  - `.wav`
  - 8MB以下
  - 5秒以下
- 写真ファイルアップロード
  - 必須
  - `.jpg` / `.png`
  - 7MB以下
- 性格・好みテキスト
  - 任意
  - 最大500文字

送信条件:
- 画像ファイル必須

ブラウザ内検証:
- ファイルサイズ検証
- 音声の再生時間検証

## 5. 共通状態設計

`frontend/src/contexts/GenerationContext.tsx`

共有している情報:
- `input: GenerateRequest | null`
- `response: GenerateResponse | null`
- `resultState: "idle" | "loading" | "done" | "error"`
- `errorCode: string | null`
- `errorMessage: string | null`

利用メソッド:
- `setInput()`
- `setLoading()`
- `setDone()`
- `setError()`
- `reset()`

補足:
- 現状 `useGenerate()` では `setInput()` は使っていない
- 画面改善時に表示用途で入力内容を再利用したい場合は、通信仕様ではなく状態保持設計の見直しになる

## 6. API呼び出し設計

### 6.1 APIクライアント共通

`frontend/src/lib/api.ts`

仕様:
- `fetch` ベース
- `Content-Type: application/json`
- タイムアウト: 360秒
- ベースURL: `VITE_BACKEND_URL`
- 非2xx時は `{ error_code, message }` を期待して `ApiError` に変換
- タイムアウト時:
  - `errorCode = "TIMEOUT"`
  - `status = 504`
- 通信失敗時:
  - `errorCode = "NETWORK_ERROR"`
  - `status = 0`

### 6.2 POST /generate

フロント呼び出し箇所:
- `frontend/src/hooks/useGenerate.ts`

バックエンド:
- `backend/src/routers/generate.py`
- `backend/src/models/request.py`
- `backend/src/models/response.py`

リクエスト:

```json
{
  "mode": "experience | production",
  "image_base64": "string",
  "audio_base64": "string | omitted",
  "user_context": "string | omitted"
}
```

制約:
- `mode`: 必須
- `image_base64`: 必須、空文字不可
- `audio_base64`: 任意
- `user_context`: 任意、最大500文字

レスポンス:

```json
{
  "session_id": "string",
  "video_url": "string",
  "state_key": "string",
  "template_id": "string",
  "template_name": "string"
}
```

画面側の動き:
- フォーム送信後に即 `navigate("/result")`
- API成功で `setDone(response)`
- API失敗で `setError(error_code, message)`

### 6.3 POST /feedback

フロント呼び出し箇所:
- `frontend/src/hooks/useFeedback.ts`
- `frontend/src/components/result/FeedbackButtons.tsx`

バックエンド:
- `backend/src/routers/feedback.py`
- `backend/src/models/request.py`
- `backend/src/models/response.py`

リクエスト:

```json
{
  "session_id": "string",
  "reaction": "good | neutral | bad"
}
```

レスポンス:

```json
{
  "reward": 1.0,
  "updated_template_id": "string"
}
```

リアクションと報酬:
- `good` -> `1.0`
- `neutral` -> `0.0`
- `bad` -> `-0.5`

画面側の動き:
- 成功時は「送信済み」表示へ切替
- 失敗時は `console.warn` のみ
- UX上はサイレントフェイル

## 7. エラー仕様

バックエンドの共通エラー形式:

```json
{
  "error_code": "string",
  "message": "string"
}
```

フロントでの扱い:
- `useGenerate()` は結果画面の `ErrorScreen` へ遷移させる
- `useFeedback()` は画面を壊さず無視する

## 8. 通信以外で使っているブラウザAPI

### 8.1 マイク

`frontend/src/hooks/useMicrophone.ts`

- `navigator.mediaDevices.getUserMedia({ audio: true })`
- `MediaRecorder`
- 最大録音時間: 5秒

### 8.2 カメラ

`frontend/src/hooks/useCamera.ts`

- `navigator.mediaDevices.getUserMedia({ video: true })`
- `video` 要素へ描画
- `canvas` 経由で Base64 化

補足:
- 現在のトップ画面主要導線ではアップロードとサンプル選択が中心で、カメラフックは将来拡張余地に近い

## 9. 今後UI改善で変更してよい範囲

以下は原則として変更可能。

- レイアウト
  - セクション配置
  - 余白
  - カラム構成
  - タブの見せ方
- ビジュアル
  - 色
  - 背景
  - タイポグラフィ
  - 影
  - 境界線
  - アニメーション
- コンポーネント
  - カード表現
  - ボタン見た目
  - フォーム見た目
  - ローディング演出
  - エラー表示
  - フィードバックUI
- 表示文言
  - ただし API の意味を変えない範囲
- アクセシビリティ改善
  - ラベル
  - フォーカス表示
  - キーボード操作

## 10. 今後UI改善で変えない範囲

以下は「通信ロジックを変えない」という前提では固定扱いにする。

- `POST /generate` を呼ぶこと
- `POST /feedback` を呼ぶこと
- リクエスト/レスポンスの JSON 形
- `VITE_BACKEND_URL` を基点に送ること
- タイムアウトや `ApiError` の基本挙動
- 生成結果のソースとして `response.video_url` を使うこと
- フィードバック送信時に `session_id` と `reaction` を送ること
- エラー時の `error_code`, `message` 前提

## 11. UI改善時の実務上のガードライン

- `useGenerate.ts`
  - API呼び出し本体は維持
  - 送信前後の見せ方だけ変える
- `useFeedback.ts`
  - サイレントフェイル方針は維持
  - ボタンUIや送信後表示は変更可
- `frontend/src/lib/api.ts`
  - 通信仕様の変更はしない
- `frontend/src/types/api.ts`
  - バックエンド契約と一致させ続ける

推奨:
- UI改善は `components/ui/`, `components/forms/`, `components/result/`, `pages/TopPage.tsx` を主対象にする
- API境界に近い `hooks/`, `lib/api.ts`, `types/api.ts` は極力触らない

## 12. 現時点の注意点

- 旧設計書 `docs/ja/Fronted_Desgin.md` には現実装とずれる箇所がある
  - モード別ページ分離
  - 一部ディレクトリ構成
  - APIクライアント責務記述
- 体験モードの鳴き声音声サンプルは現在リクエストに載っていない
- `GenerationContext.input` は未活用
- `/experience` と `/production` は残っているが、実体ページではなくトップへ戻すだけ

## 13. UI改善の優先対象

優先度高:
- `frontend/src/pages/TopPage.tsx`
- `frontend/src/components/forms/ExperienceForm.tsx`
- `frontend/src/components/forms/ProductionForm.tsx`
- `frontend/src/components/result/LoadingScreen.tsx`
- `frontend/src/components/result/ErrorScreen.tsx`
- `frontend/src/components/result/FeedbackButtons.tsx`

優先度低:
- `frontend/src/hooks/useGenerate.ts`
- `frontend/src/hooks/useFeedback.ts`
- `frontend/src/lib/api.ts`
- `frontend/src/types/api.ts`

