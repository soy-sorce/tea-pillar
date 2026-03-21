"""Unit tests for Vertex image preprocessing."""

from __future__ import annotations

from src.exceptions import InvalidInputError
from src.services.cat_model.image_preprocessor import VertexImagePreprocessor


def test_preprocess_rejects_invalid_base64() -> None:
    preprocessor = VertexImagePreprocessor()

    try:
        preprocessor.preprocess("x")
    except InvalidInputError as exc:
        assert exc.error_code == "INVALID_INPUT"
    else:
        raise AssertionError("InvalidInputError was not raised")
