"""Image preprocessing helpers for Vertex requests."""

import base64
import binascii
import io
from typing import Final, Self

import structlog
from PIL import Image, ImageOps, UnidentifiedImageError

from src.exceptions import InvalidInputError

logger = structlog.get_logger(__name__)

VERTEX_IMAGE_TARGET_BYTES: Final[int] = 700_000
INITIAL_MAX_DIMENSION: Final[int] = 1280
MIN_MAX_DIMENSION: Final[int] = 512
INITIAL_QUALITY: Final[int] = 85
MIN_QUALITY: Final[int] = 45
QUALITY_STEP: Final[int] = 10
DIMENSION_SHRINK_RATIO: Final[float] = 0.85


class VertexImagePreprocessor:
    """Shrink and recompress uploaded images before Vertex prediction."""

    def preprocess(self: Self, image_base64: str) -> str:
        """Return a base64 image that better fits the Vertex request limit."""
        try:
            raw_bytes = base64.b64decode(image_base64, validate=True)
        except (ValueError, binascii.Error) as exc:
            logger.warning("vertex_image_preprocess_invalid_base64")
            raise InvalidInputError(
                message="画像データの形式が不正です",
                detail=str(exc),
            ) from exc

        logger.debug(
            "vertex_image_preprocess_start",
            raw_byte_size=len(raw_bytes),
        )

        try:
            with Image.open(io.BytesIO(raw_bytes)) as opened_image:
                image = ImageOps.exif_transpose(opened_image).convert("RGB")
        except (UnidentifiedImageError, OSError) as exc:
            logger.warning(
                "vertex_image_preprocess_open_failed",
                raw_byte_size=len(raw_bytes),
            )
            raise InvalidInputError(
                message="画像データの形式が不正です",
                detail="image bytes could not be decoded",
            ) from exc

        original_size = image.size
        max_dimension = INITIAL_MAX_DIMENSION
        quality = INITIAL_QUALITY
        processed_bytes = self._encode(
            image=image,
            max_dimension=max_dimension,
            quality=quality,
        )

        while len(processed_bytes) > VERTEX_IMAGE_TARGET_BYTES:
            if quality > MIN_QUALITY:
                quality = max(quality - QUALITY_STEP, MIN_QUALITY)
            elif max_dimension > MIN_MAX_DIMENSION:
                max_dimension = max(
                    int(max_dimension * DIMENSION_SHRINK_RATIO),
                    MIN_MAX_DIMENSION,
                )
            else:
                break
            processed_bytes = self._encode(
                image=image,
                max_dimension=max_dimension,
                quality=quality,
            )

        logger.info(
            "vertex_image_preprocess_done",
            original_size=original_size,
            original_byte_size=len(raw_bytes),
            processed_byte_size=len(processed_bytes),
            max_dimension=max_dimension,
            quality=quality,
        )
        return base64.b64encode(processed_bytes).decode("utf-8")

    def _encode(self: Self, image: Image.Image, max_dimension: int, quality: int) -> bytes:
        """Resize and encode to JPEG bytes."""
        resized = image.copy()
        resized.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        resized.save(buffer, format="JPEG", optimize=True, quality=quality)
        return buffer.getvalue()
