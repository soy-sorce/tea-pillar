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

## Phase 1 readiness

The codebase is prepared for Phase 1, but dependency installation is intentionally
left to the user.

Recommended runtime:

- Python `3.11`
- app entrypoint: `src.app:app`

Required runtime libraries to add:

- `fastapi`
- `uvicorn[standard]`
- `pydantic`
- `pydantic-settings`
- `structlog`
- `google-cloud-aiplatform`
- `google-cloud-firestore`
- `google-cloud-storage`
- `vertexai`

Recommended dev libraries to add:

- `ruff`
- `mypy`
- `pytest`
- `pytest-asyncio`
- `pytest-mock`
- `pre-commit`

Recommended local verification flow after dependency install:

```bash
cd backend
uv sync
uv run uvicorn src.app:app --reload --port 8080
```

Checks to run:

```bash
cd backend
uv run python -m compileall src
uv run ruff check src
uv run mypy src
```
