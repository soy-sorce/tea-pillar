"""HTTP app for local and containerized prediction serving."""

from __future__ import annotations

from threading import Lock

from fastapi import FastAPI

from src.predictor import Predictor
from src.schemas import PredictionRequest

app = FastAPI(
    title="nekkoflix model endpoint",
    version="0.1.0",
    description="Local-compatible prediction service for the nekkoflix custom model.",
)

_predictor: Predictor | None = None
_predictor_lock = Lock()


def _get_predictor() -> Predictor:
    """Lazily initialize the heavy predictor after the container becomes healthy."""
    global _predictor
    if _predictor is None:
        with _predictor_lock:
            if _predictor is None:
                _predictor = Predictor()
    return _predictor


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "predictor_loaded": "true" if _predictor is not None else "false"}


@app.post("/predict", response_model=None)
async def predict(request: PredictionRequest) -> dict[str, object]:
    """Run model prediction and return the contract response."""
    response = _get_predictor().predict(request=request)
    return response.to_dict()
