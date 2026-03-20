"""Shared pytest fixtures for backend tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


@pytest.fixture
def project_root() -> Path:
    """Return the backend project root."""
    return BACKEND_ROOT
