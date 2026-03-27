"""Shared pytest fixtures for model tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

MODEL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[2]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

if str(MODEL_ROOT) not in sys.path:
    sys.path.insert(0, str(MODEL_ROOT))


@pytest.fixture(autouse=True)
def reset_model_rate_limit_state() -> None:
    """Isolate in-memory limiter state per test."""
    from src.rate_limit import reset_rate_limit_state

    reset_rate_limit_state()
