"""Local smoke test for backend local model fallback initialization."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def main() -> int:
    """Initialize the real local fallback predictor and report success or failure."""
    from src.services.cat_model.local_runtime.predictor import LocalCatModelPredictor

    LocalCatModelPredictor()
    print("Backend local model fallback initialization smoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
