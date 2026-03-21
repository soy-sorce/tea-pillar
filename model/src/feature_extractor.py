"""Real feature extraction for the model endpoint.

This module ports the v1 image feature extraction logic from
`tea-pillar-ML-analysis/script/v1/modeling/script/training_workflows.py`
to the runtime endpoint. The external contract stays unchanged:

- input: base64 image/audio
- output: `features` and `aux_labels`

For v1, `emotion / pose / clip` are executed in-process. `meow` remains
optional and returns `None` until the audio model is integrated.
"""

from __future__ import annotations

import base64
import io
import math
from collections.abc import Callable, Mapping
from typing import Any, Final, Self, TypedDict

import numpy as np
from google.cloud.storage import Client as StorageClient

from src.schemas import PredictionRequest

EMOTION_MODEL_ID: Final[str] = "semihdervis/cat-emotion-classifier"
POSE_MODEL_ID: Final[str] = "usyd-community/vitpose-plus-small"
CLIP_MODEL_ID: Final[str] = "openai/clip-vit-base-patch32"
EMOTION_PROCESSOR_FALLBACK_ID: Final[str] = "google/vit-base-patch16-224-in21k"

EMOTION_LABELS: Final[list[str]] = ["happy", "sad", "angry"]
CLIP_PROMPTS: Final[list[str]] = [
    "attentive cat",
    "relaxed cat",
    "stressed cat",
    "playful cat",
    "sleepy cat",
    "curious cat",
    "alert cat",
    "comfortable cat",
]
POSE_FEATURE_NAMES: Final[list[str]] = [
    "pose_mean_confidence",
    "pose_x_span",
    "pose_y_span",
    "pose_area_ratio",
    "pose_centroid_x",
    "pose_centroid_y",
    "pose_pc1_variance",
    "pose_pc2_variance",
    "pose_pc_ratio",
    "pose_principal_angle_sin",
    "pose_principal_angle_cos",
    "pose_compactness",
]


class _ScoreRow(TypedDict):
    label: str
    score: float


class FeatureExtractor:
    """Extract v1 features using the same models as ML-analysis."""

    def __init__(self: Self, device: str | None = None) -> None:
        self._runtime = _ModelRuntime(device=device)

    def extract(
        self: Self, request: PredictionRequest
    ) -> tuple[dict[str, float], dict[str, str | None]]:
        """Extract features and auxiliary labels from endpoint request."""
        image = _load_request_image(request)
        emotion_scores = self._runtime.extract_emotion_scores(image)
        clip_scores = self._runtime.extract_clip_scores(image)
        pose_features = self._runtime.extract_pose_features(image)

        features = {**emotion_scores, **clip_scores, **pose_features}
        emotion_label = max(EMOTION_LABELS, key=lambda label: emotion_scores[f"emotion_{label}"])
        clip_top_label = max(
            CLIP_PROMPTS,
            key=lambda label: clip_scores[f"clip_{label.replace(' ', '_')}"],
        )
        aux_labels = {
            "emotion_label": emotion_label,
            "clip_top_label": clip_top_label.replace(" ", "_"),
            # v1 keeps meow optional. Audio integration can fill this later without
            # changing the backend/model contract.
            "meow_label": None,
        }
        return features, aux_labels


class _ModelRuntime:
    """Lazy-loaded Hugging Face model bundle."""

    def __init__(self: Self, device: str | None = None) -> None:
        (
            self._torch,
            auto_image_processor,
            auto_model_for_image_classification,
            auto_processor,
            clip_model_cls,
            clip_processor_cls,
            vit_image_processor,
            vit_pose_cls,
            pil_image,
        ) = _import_runtime_dependencies()

        self._image_type = pil_image.Image
        self.device = device or ("cuda" if self._torch.cuda.is_available() else "cpu")

        self.emotion_processor = self._load_emotion_processor(
            auto_image_processor=auto_image_processor,
            vit_image_processor=vit_image_processor,
        )
        self.emotion_model = auto_model_for_image_classification.from_pretrained(
            EMOTION_MODEL_ID
        ).to(self.device)
        self.clip_processor = clip_processor_cls.from_pretrained(CLIP_MODEL_ID)
        self.clip_model = clip_model_cls.from_pretrained(CLIP_MODEL_ID).to(self.device)
        self.pose_processor = auto_processor.from_pretrained(POSE_MODEL_ID)
        self.pose_model = vit_pose_cls.from_pretrained(POSE_MODEL_ID).to(self.device)

        self.emotion_model.eval()
        self.clip_model.eval()
        self.pose_model.eval()

    def _load_emotion_processor(
        self: Self,
        *,
        auto_image_processor: Any,
        vit_image_processor: Any,
    ) -> Any:
        try:
            return auto_image_processor.from_pretrained(EMOTION_MODEL_ID, use_fast=False)
        except Exception:
            return vit_image_processor.from_pretrained(
                EMOTION_PROCESSOR_FALLBACK_ID,
                use_fast=False,
            )

    def extract_emotion_scores(self: Self, image: Any) -> dict[str, float]:
        inputs = self.emotion_processor(images=image, return_tensors="pt")
        batch = _move_to_device(inputs, self.device)
        with self._torch.no_grad():
            outputs = self.emotion_model(**batch)
            probs = self._torch.softmax(outputs.logits[0], dim=0).cpu().numpy()

        raw_id2label = self.emotion_model.config.id2label
        rows: list[_ScoreRow] = [
            {
                "label": str(raw_id2label[idx]).lower(),
                "score": float(score),
            }
            for idx, score in enumerate(probs)
        ]
        normalized = _normalize_scores(rows, EMOTION_LABELS)
        return {f"emotion_{label}": score for label, score in normalized.items()}

    def extract_clip_scores(self: Self, image: Any) -> dict[str, float]:
        inputs = self.clip_processor(
            text=CLIP_PROMPTS,
            images=image,
            return_tensors="pt",
            padding=True,
        )
        batch = _move_to_device(inputs, self.device)
        with self._torch.no_grad():
            outputs = self.clip_model(**batch)
            logits = outputs.logits_per_image[0]
            probs = logits.softmax(dim=0).cpu().numpy()
        return {
            f"clip_{prompt.replace(' ', '_')}": float(score)
            for prompt, score in zip(CLIP_PROMPTS, probs, strict=True)
        }

    def extract_pose_features(self: Self, image: Any) -> dict[str, float]:
        width, height = image.size
        boxes = [[[0.0, 0.0, float(width), float(height)]]]
        inputs = self.pose_processor(image, boxes=boxes, return_tensors="pt")
        batch = _move_to_device(inputs, self.device)
        dataset_index = self._torch.tensor([3], device=self.device)

        with self._torch.no_grad():
            outputs = self.pose_model(**batch, dataset_index=dataset_index)

        pose_results = self.pose_processor.post_process_pose_estimation(outputs, boxes=boxes)
        if not pose_results or not pose_results[0]:
            return {name: 0.0 for name in POSE_FEATURE_NAMES}

        result = pose_results[0][0]
        keypoints = result["keypoints"].cpu().numpy()
        scores = result["scores"].cpu().numpy()
        return _compress_pose_keypoints(keypoints, scores, width, height)


def _import_runtime_dependencies() -> tuple[Any, Any, Any, Any, Any, Any, Any, Any, Any]:
    """Import heavyweight runtime deps lazily so config inspection still works."""
    try:
        import torch
        from PIL import Image
        from transformers import (
            AutoImageProcessor,
            AutoModelForImageClassification,
            AutoProcessor,
            CLIPModel,
            CLIPProcessor,
            ViTImageProcessor,
            VitPoseForPoseEstimation,
        )
    except ImportError as exc:
        raise RuntimeError(
            "model runtime dependencies are missing. Install torch, transformers, and pillow."
        ) from exc

    return (
        torch,
        AutoImageProcessor,
        AutoModelForImageClassification,
        AutoProcessor,
        CLIPModel,
        CLIPProcessor,
        ViTImageProcessor,
        VitPoseForPoseEstimation,
        Image,
    )


def _load_request_image(request: PredictionRequest) -> Any:
    """Load an image from GCS when available, otherwise fall back to base64."""
    loaders: list[Callable[[], Any]] = []
    if request.image_gcs_uri:
        loaders.append(lambda: _load_gcs_image(request.image_gcs_uri or ""))
    if request.image_base64:
        loaders.append(lambda: _decode_base64_image(request.image_base64 or ""))

    for loader in loaders:
        try:
            return loader()
        except Exception:
            continue

    raise ValueError("request image is missing or unreadable")


def _decode_base64_image(value: str) -> Any:
    """Decode a base64 image into a PIL RGB image."""
    image_bytes = base64.b64decode(value.encode("utf-8"), validate=False)
    (_, _, _, _, _, _, _, _, pil_image) = _import_runtime_dependencies()
    return pil_image.open(io.BytesIO(image_bytes)).convert("RGB")


def _load_gcs_image(gcs_uri: str) -> Any:
    """Load an image from a gs:// URI."""
    if not gcs_uri.startswith("gs://"):
        raise ValueError("gcs_uri must start with gs://")

    path = gcs_uri.removeprefix("gs://")
    bucket_name, _, blob_name = path.partition("/")
    if not bucket_name or not blob_name:
        raise ValueError("gcs_uri must include bucket and object path")

    client = StorageClient()
    blob = client.bucket(bucket_name).blob(blob_name)
    image_bytes = blob.download_as_bytes()
    (_, _, _, _, _, _, _, _, pil_image) = _import_runtime_dependencies()
    return pil_image.open(io.BytesIO(image_bytes)).convert("RGB")


def _move_to_device(inputs: Mapping[str, Any], device: str) -> dict[str, Any]:
    """Move tensor-like entries to the target device."""
    return {
        key: value.to(device) if hasattr(value, "to") else value for key, value in inputs.items()
    }


def _normalize_scores(
    rows: list[_ScoreRow],
    expected_labels: list[str],
) -> dict[str, float]:
    """Normalize possibly sparse classifier output to a fixed label set."""
    score_map = {str(row["label"]).lower(): float(row["score"]) for row in rows}
    return {label: score_map.get(label, 0.0) for label in expected_labels}


def _compress_pose_keypoints(
    keypoints: np.ndarray,
    scores: np.ndarray,
    width: int,
    height: int,
) -> dict[str, float]:
    """Compress raw keypoints into the 12D pose feature space."""
    valid = scores > 0.05
    if int(valid.sum()) < 2:
        return {name: 0.0 for name in POSE_FEATURE_NAMES}

    pts = keypoints[valid]
    conf = scores[valid]

    x_norm = pts[:, 0] / max(width, 1)
    y_norm = pts[:, 1] / max(height, 1)

    x_span = float(np.max(x_norm) - np.min(x_norm))
    y_span = float(np.max(y_norm) - np.min(y_norm))
    area_ratio = float(x_span * y_span)
    centroid_x = float(np.average(x_norm, weights=conf))
    centroid_y = float(np.average(y_norm, weights=conf))

    centered = np.stack([x_norm - centroid_x, y_norm - centroid_y], axis=1)
    weighted = centered * conf[:, None]
    cov = np.cov(weighted.T)
    eigvals, eigvecs = np.linalg.eigh(cov)
    order = np.argsort(eigvals)[::-1]
    eigvals = eigvals[order]
    eigvecs = eigvecs[:, order]

    pc1 = float(max(float(eigvals[0]), 0.0))
    pc2 = float(max(float(eigvals[1]), 0.0))
    ratio = float(pc1 / (pc2 + 1e-6))
    principal_angle = math.atan2(float(eigvecs[1, 0]), float(eigvecs[0, 0]))
    compactness = float((pc1 + pc2) / (area_ratio + 1e-6))

    values = [
        float(np.mean(conf)),
        x_span,
        y_span,
        area_ratio,
        centroid_x,
        centroid_y,
        pc1,
        pc2,
        ratio,
        math.sin(principal_angle),
        math.cos(principal_angle),
        compactness,
    ]
    return dict(zip(POSE_FEATURE_NAMES, values, strict=True))
