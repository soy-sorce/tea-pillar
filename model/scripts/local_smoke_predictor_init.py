"""Local smoke test for real Predictor initialization.

This script intentionally imports the real Predictor so we can fail fast on
missing runtime dependencies such as lightgbm before building/deploying.
"""

from __future__ import annotations

import sys
from pathlib import Path

MODEL_ROOT = Path(__file__).resolve().parents[1]

if str(MODEL_ROOT) not in sys.path:
    sys.path.insert(0, str(MODEL_ROOT))


def main() -> int:
    """Initialize the real Predictor and report success or failure."""
    from src.predictor import Predictor

    Predictor()
    print("Predictor initialization smoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
