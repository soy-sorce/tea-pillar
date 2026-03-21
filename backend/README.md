# backend

FastAPI backend for nekkoflix.

Current implementation follows:

- `docs/ja/Backend_Design.md`
- `docs/ja/High_Level_Design.md`
- `docs/ja/Requirements_Definition.md`
- `docs/ja/MODELING.md`

Notes:

- The backend is aligned to the current `MODELING.md` v1 design.
- The old `BasicDesign.md` / `requirements_v1.md` references were normalized to the
  current filenames above.
- External service identifiers such as the Vertex AI endpoint ID and GCS bucket name
  are intentionally left blank in `.env.example` until they are finalized.

## Runtime

- Python `3.11`
- app entrypoint: `src.app:app`

Install dependencies:

```bash
cd backend
uv sync --extra dev
```

Local app startup:

```bash
cd backend
cp .env.example .env
uv run uvicorn src.app:app --reload --port 8080
```

Notes:

- Most unit and route tests should not require real GCP resources.
- Real external IDs in `.env` are only needed when manually exercising Vertex AI,
  Gemini, Veo, Firestore, and GCS integrations outside mocks.

## Developer Setup For Tests

Recommended baseline checks:

```bash
cd backend
uv run python -m compileall src tests
uv run ruff check src tests
uv run mypy src
```

Run all tests:

```bash
cd backend
uv run pytest
```

Run by scope:

```bash
cd backend
uv run pytest tests/unit
uv run pytest tests/integration
```

Useful pytest filters:

```bash
cd backend
uv run pytest -k orchestrator
uv run pytest tests/integration/test_feedback_route.py
```

## Current Test Coverage

Already implemented:

- `tests/unit/test_state_key_builder.py`
  - state key format
  - `meow_label=None` fallback to `unknown`
- `tests/unit/test_prompt_builder.py`
  - template, labels, features, and user context are embedded into Gemini input
  - missing `user_context` fallback text
- `tests/unit/test_ucb.py`
  - highest `predicted_reward + UCB bonus` is selected
  - update delegation to repository
- `tests/integration/test_orchestrator.py`
  - happy path for end-to-end orchestration with fakes
  - failure path marks session as failed
- `tests/integration/test_feedback_route.py`
  - feedback success path
  - non-`done` session returns `409`

## Test Plan To Implement

The list below is the recommended target coverage for `backend/tests`. It is grouped
by module so new tests can be added incrementally without changing production code
first.

### 1. API / App Layer

Target files:

- `tests/integration/test_app_routes.py`
- `tests/integration/test_generate_route.py`
- `tests/integration/test_health_route.py`
- `tests/integration/test_error_handlers.py`

Cases:

- `GET /` returns service name, status, and environment
- `GET /health` returns `ok` and environment
- `GET /favicon.ico` returns `204`
- request middleware adds `X-Request-ID`
- invalid request body on `POST /generate` returns `400 INVALID_INPUT`
- invalid request body on `POST /feedback` returns `400 INVALID_INPUT`
- application exceptions are converted to expected status and error payload
- unexpected exceptions are surfaced in a controlled way if a generic handler is added later

### 2. Request / Response Schema Validation

Target files:

- `tests/unit/test_request_models.py`
- `tests/unit/test_response_models.py`

Cases:

- `GenerateRequest.mode` accepts only `experience` and `production`
- `GenerateRequest.image_base64` rejects empty string
- `GenerateRequest.user_context` accepts `None`
- `GenerateRequest.user_context` rejects length over `500`
- `FeedbackRequest.session_id` rejects empty string
- `FeedbackRequest.reaction` accepts only `good`, `neutral`, `bad`
- response models serialize expected required fields

### 3. Orchestrator

Target file:

- `tests/integration/test_orchestrator.py`

Add cases:

- `create_session` is called before any external service work
- `complete_session` stores final state after all downstream steps succeed
- `audio_base64=None` path is forwarded correctly to cat model client
- `user_context=None` path is forwarded correctly to Gemini client
- generated response includes `session_id`, `video_url`, `state_key`, `template_id`, `template_name`
- each handled exception type triggers `fail_session`
- if `fail_session` itself raises `FirestoreError`, the original exception is still re-raised
- `state_key` and `template_id` are partially absent when failure happens before those steps

Failure matrix to cover:

- `FirestoreError` during `create_session`
- `VertexAITimeoutError`
- `VertexAIError`
- `TemplateSelectionError`
- `GeminiError`
- `VeoGenerationError`
- `VeoTimeoutError`
- `NotConfiguredError`

### 4. Feedback Route

Target file:

- `tests/integration/test_feedback_route.py`

Add cases:

- `neutral` maps to reward `0.0`
- `bad` maps to reward `-0.5`
- session not found returns `404`
- session with missing `template_id` returns `409`
- session with missing `state_key` returns `409`
- `save_feedback` failure returns `500`
- bandit update failure returns `500`
- invalid `reaction` payload returns `400`

### 5. Firestore Client

Target file:

- `tests/unit/test_firestore_client.py`

Cases:

- `create_session` writes expected fields and initial status `generating`
- `complete_session` writes `done`, `state_key`, `template_id`, `video_gcs_uri`
- `fail_session` writes `failed` and `error`
- `get_session` returns parsed `SessionDocument`
- missing session raises `ResourceNotFoundError`
- `get_bandit_entries_by_state_key` returns dict keyed by `template_id`
- `update_bandit_entry` creates a new entry when document does not exist
- `update_bandit_entry` increments `selection_count`, `cumulative_reward`, `mean_reward`
- `get_active_templates` filters active records and sorts by `template_id`
- `save_feedback` writes expected document
- `_require_snapshot_dict` raises `FirestoreError` on `None`
- Google API exceptions are wrapped as `FirestoreError`

### 6. Bandit Repository

Target file:

- `tests/unit/test_bandit_repository.py`

Cases:

- repository delegates reads and writes to `FirestoreClient`
- argument names and values are passed through unchanged

This layer is thin, but a small delegation test keeps refactors safe.

### 7. UCB Bandit

Target file:

- `tests/unit/test_ucb.py`

Add cases:

- empty active template list raises `TemplateSelectionError`
- missing predicted reward for an active template raises `TemplateSelectionError`
- unseen template uses default exploration path
- `_calculate_ucb_bonus` is `0` when `total_n` is effectively cold start
- larger `selection_count` reduces bonus
- `bandit_ucb_alpha` changes bonus magnitude
- tie behavior is deterministic and documented by test

### 8. State Key Builder

Target file:

- `tests/unit/test_state_key_builder.py`

Add cases:

- output uses exact ordering `meow_emotion_clip`
- special labels are concatenated as-is without silent normalization
- empty string labels are preserved if upstream ever sends them

### 9. Cat Model Client

Target file:

- `tests/unit/test_cat_model_client.py`

Cases:

- missing `gcp_project_id` or `vertex_endpoint_id` raises `NotConfiguredError`
- request payload forwards `image_base64`, optional `audio_base64`, and `candidate_video_ids`
- `predict()` parses endpoint output into `CatFeatures`
- `meow_label` may be `None`
- feature values and predicted rewards are cast to `float`
- `DeadlineExceeded` maps to `VertexAITimeoutError`
- `RetryError` maps to `VertexAITimeoutError`
- `GoogleAPICallError` maps to `VertexAIError`
- malformed endpoint payload currently fails loudly; add tests before hardening parser

### 10. Gemini Prompt Builder

Target file:

- `tests/unit/test_prompt_builder.py`

Add cases:

- features are rendered in sorted key order
- prompt always includes system instruction and constraints
- optional `user_context` fallback text remains stable
- `meow_label` non-null path is included correctly

### 11. Gemini Client

Target file:

- `tests/unit/test_gemini_client.py`

Cases:

- missing `gcp_project_id` raises `NotConfiguredError`
- `PromptBuilder.build()` output is passed to model
- model name from settings is used
- generation config includes expected token and temperature settings
- successful response returns stripped `response.text`
- `TimeoutError`, `DeadlineExceeded`, `RetryError` map to `GeminiError`
- `GoogleAPICallError` maps to `GeminiError`

### 12. Veo Client

Target file:

- `tests/unit/test_veo_client.py`

Cases:

- missing `gcp_project_id` or `gcs_bucket_name` raises `NotConfiguredError`
- request payload includes prompt and `output_gcs_uri`
- `predict()` API errors map to `VeoGenerationError` / `VeoTimeoutError`
- polling stops and returns URI when operation completes successfully
- polling raises `VeoTimeoutError` when elapsed time exceeds timeout
- polling raises `VeoGenerationError` when operation finishes with non-zero error
- `_extract_gcs_uri` supports raw `gs://...` response
- `_extract_gcs_uri` supports JSON with `gcs_uri`
- `_extract_gcs_uri` supports JSON with `output_gcs_uri`
- `_extract_gcs_uri` supports JSON with `uri`
- `_extract_gcs_uri` supports artifact list payload
- unknown response format raises `VeoGenerationError`

### 13. Signed URL Generator

Target file:

- `tests/unit/test_signed_url.py`

Cases:

- missing `gcp_project_id` raises `NotConfiguredError`
- `gs://bucket/path/file.mp4` is split into bucket and blob correctly
- expiration hours from settings are passed to `generate_signed_url`
- generated URL string is returned as-is

### 14. Exception Classes

Target file:

- `tests/unit/test_exceptions.py`

Cases:

- each exception exposes expected `error_code`, default `message`, and `status_code`
- constructor overrides `message` and `detail`
- `to_response_content()` does not leak `detail`

### 15. Config

Target file:

- `tests/unit/test_config.py`

Cases:

- defaults from `Settings()` match `.env.example`
- environment variables override defaults
- `get_settings()` is cached
- `default_candidate_video_ids` produces `video-1` through `video-10`

### 16. Logging Configuration

Target file:

- `tests/unit/test_logging_config.py`

Cases:

- logging setup can be called repeatedly without breaking
- expected processors / JSON logging behavior are configured if this module grows

### 17. End-to-End Mocked Flow

Target file:

- `tests/integration/test_generate_flow.py`

Cases:

- `POST /generate` with dependency or monkeypatch fakes returns full happy-path payload
- route-level `POST /generate` propagates orchestrator failures to correct HTTP status
- request validation and response contract are checked at FastAPI boundary

## Suggested Test Order

Implement in this order to get the fastest confidence:

1. route and schema validation tests
2. Firestore client tests
3. Cat model / Gemini / Veo / signed URL client tests
4. orchestrator failure matrix
5. remaining thin-layer tests

## Test Design Principles

- Prefer unit tests with fakes or monkeypatches over real GCP calls.
- Keep external API contract parsing covered with narrow tests around each client.
- Add one route-level integration test per public endpoint, then push most edge cases
  into unit tests below the router.
- When a bug is found, reproduce it first with the smallest failing test near the
  responsible layer.
