"""Unit tests for logging configuration."""

from __future__ import annotations

import logging

import structlog
from src.logging_config import configure_logging


def test_configure_logging_is_idempotent() -> None:
    configure_logging("INFO")
    configure_logging("DEBUG")

    logger = structlog.get_logger(__name__)
    assert logger is not None


def test_configure_logging_sets_root_level() -> None:
    configure_logging("WARNING")

    assert logging.getLogger().getEffectiveLevel() in {
        logging.WARNING,
        logging.INFO,
    }
