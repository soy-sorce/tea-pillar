"""Artifact loading utilities."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ARTIFACT_DIR = Path(__file__).resolve().parent.parent / "artifacts"
_FEATURE_COLUMNS_PATH = ARTIFACT_DIR / "feature_columns.json"
_VIDEO_ID_MAPPING_PATH = ARTIFACT_DIR / "video_id_mapping.json"
_TRAINING_METADATA_PATH = ARTIFACT_DIR / "training_metadata.json"
_CLIP_PROMPTS_PATH = ARTIFACT_DIR / "clip_prompts.json"
_REGRESSOR_PATH = ARTIFACT_DIR / "reward_regressor.joblib"


@dataclass(slots=True)
class ArtifactBundle:
    """Loaded model artifacts."""

    feature_columns: list[str]
    video_id_mapping: list[str]
    training_metadata: dict[str, Any]
    clip_prompts: dict[str, str]
    regressor: object


def load_artifacts() -> ArtifactBundle | None:
    """Load artifacts if all required files are present.

    Returns `None` when artifacts are not ready yet.
    """
    required_paths = (
        _FEATURE_COLUMNS_PATH,
        _VIDEO_ID_MAPPING_PATH,
        _TRAINING_METADATA_PATH,
        _CLIP_PROMPTS_PATH,
        _REGRESSOR_PATH,
    )
    if not all(path.exists() for path in required_paths):
        return None

    import joblib

    return ArtifactBundle(
        feature_columns=_read_json_list(_FEATURE_COLUMNS_PATH),
        video_id_mapping=_read_json_list(_VIDEO_ID_MAPPING_PATH),
        training_metadata=_read_json_dict(_TRAINING_METADATA_PATH),
        clip_prompts=_read_json_dict(_CLIP_PROMPTS_PATH),
        regressor=joblib.load(_REGRESSOR_PATH),
    )


def _read_json_list(path: Path) -> list[str]:
    """Read a list[str] JSON file."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [str(item) for item in payload]


def _read_json_dict(path: Path) -> dict[str, Any]:
    """Read a dict JSON file."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {str(key): value for key, value in payload.items()}
