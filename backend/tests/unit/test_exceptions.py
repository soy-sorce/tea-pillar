"""Unit tests for custom exceptions."""

from __future__ import annotations

from src.exceptions import (
    FirestoreError,
    GeminiError,
    InvalidInputError,
    NekkoflixBaseError,
    NotConfiguredError,
    ResourceNotFoundError,
    SessionConflictError,
    TemplateSelectionError,
    VeoGenerationError,
    VeoTimeoutError,
    VertexAIError,
    VertexAITimeoutError,
)


def test_base_error_serializes_safe_response() -> None:
    error = NekkoflixBaseError(message="safe", detail="secret")

    assert error.to_response_content() == {
        "error_code": "INTERNAL_ERROR",
        "message": "safe",
    }
    assert error.detail == "secret"


def test_specific_exceptions_expose_expected_metadata() -> None:
    assert InvalidInputError().error_code == "INVALID_INPUT"
    assert ResourceNotFoundError().status_code == 404
    assert SessionConflictError().status_code == 409
    assert VertexAITimeoutError().error_code == "VERTEX_TIMEOUT"
    assert VertexAIError().error_code == "VERTEX_FAILED"
    assert GeminiError().error_code == "GEMINI_FAILED"
    assert VeoGenerationError().error_code == "VEO_FAILED"
    assert VeoTimeoutError().status_code == 504
    assert FirestoreError().error_code == "FIRESTORE_FAILED"
    assert TemplateSelectionError().error_code == "TEMPLATE_SELECTION_FAILED"
    assert NotConfiguredError().error_code == "NOT_CONFIGURED"


def test_exception_constructor_overrides_message_and_detail() -> None:
    error = FirestoreError(message="custom", detail="root cause")

    assert error.message == "custom"
    assert error.detail == "root cause"
