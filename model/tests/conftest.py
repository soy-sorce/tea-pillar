"""Shared pytest fixtures for model tests."""

from __future__ import annotations

import sys
from pathlib import Path

MODEL_ROOT = Path(__file__).resolve().parents[1]

if str(MODEL_ROOT) not in sys.path:
    sys.path.insert(0, str(MODEL_ROOT))
