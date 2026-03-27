"""Download Hugging Face runtime models during backend Docker build."""

from __future__ import annotations

from transformers import (
    AutoImageProcessor,
    AutoModelForImageClassification,
    AutoProcessor,
    CLIPModel,
    CLIPProcessor,
    ViTImageProcessor,
    VitPoseForPoseEstimation,
)

EMOTION_MODEL_ID = "semihdervis/cat-emotion-classifier"
POSE_MODEL_ID = "usyd-community/vitpose-plus-small"
CLIP_MODEL_ID = "openai/clip-vit-base-patch32"
EMOTION_PROCESSOR_FALLBACK_ID = "google/vit-base-patch16-224-in21k"


def main() -> None:
    """Download all Hugging Face assets required at runtime."""
    try:
        AutoImageProcessor.from_pretrained(EMOTION_MODEL_ID, use_fast=False)
    except Exception:
        ViTImageProcessor.from_pretrained(EMOTION_PROCESSOR_FALLBACK_ID, use_fast=False)

    AutoModelForImageClassification.from_pretrained(EMOTION_MODEL_ID)
    CLIPProcessor.from_pretrained(CLIP_MODEL_ID)
    CLIPModel.from_pretrained(CLIP_MODEL_ID)
    AutoProcessor.from_pretrained(POSE_MODEL_ID)
    VitPoseForPoseEstimation.from_pretrained(POSE_MODEL_ID)


if __name__ == "__main__":
    main()
