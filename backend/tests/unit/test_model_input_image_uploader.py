"""Unit tests for model input image uploading."""

from __future__ import annotations

from src.config import Settings
from src.exceptions import InvalidInputError
from src.services.cat_model.input_image_uploader import ModelInputImageUploader


def test_upload_base64_image_rejects_invalid_base64() -> None:
    uploader = ModelInputImageUploader(
        settings=Settings(model_input_bucket_name="bucket-name"),
    )

    try:
        uploader.upload_base64_image("x")
    except InvalidInputError as exc:
        assert exc.error_code == "INVALID_INPUT"
    else:
        raise AssertionError("InvalidInputError was not raised")
