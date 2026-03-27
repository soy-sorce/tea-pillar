"""Artifact loading utilities."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

ARTIFACT_DIR = Path(__file__).resolve().parent.parent / "artifacts"
_FEATURE_COLUMNS_PATH = ARTIFACT_DIR / "feature_columns.json"
_FEATURE_SCHEMA_PATH = ARTIFACT_DIR / "feature_schema.json"
_QUERY_MAPPING_PATH = ARTIFACT_DIR / "query_mapping.json"
_TRAINING_METADATA_PATH = ARTIFACT_DIR / "training_metadata.json"
_BANDIT_PARAMS_PATH = ARTIFACT_DIR / "bandit_params.json"
_REWARD_FORMULA_PATH = ARTIFACT_DIR / "reward_formula.json"
_REGRESSOR_PATH = ARTIFACT_DIR / "reward_regressor.joblib"


@dataclass(slots=True)
class ArtifactBundle:
    """Loaded model artifacts."""

    feature_columns: list[str]
    feature_schema: dict[str, Any]
    query_mapping: dict[str, Any]
    training_metadata: dict[str, Any]
    bandit_params: dict[str, Any]
    reward_formula: dict[str, Any]
    regressor: object
    source: str


def load_artifacts() -> ArtifactBundle | None:
    """Load artifacts from a local directory or Hugging Face snapshot.

    Returns `None` when artifacts are not ready yet.
    """
    artifact_dir = resolve_artifact_dir()
    if artifact_dir is None:
        return None

    feature_columns_path = artifact_dir / "feature_columns.json"
    feature_schema_path = artifact_dir / "feature_schema.json"
    query_mapping_path = artifact_dir / "query_mapping.json"
    training_metadata_path = artifact_dir / "training_metadata.json"
    bandit_params_path = artifact_dir / "bandit_params.json"
    reward_formula_path = artifact_dir / "reward_formula.json"
    regressor_path = artifact_dir / "reward_regressor.joblib"

    required_paths = (
        feature_columns_path,
        feature_schema_path,
        query_mapping_path,
        training_metadata_path,
        bandit_params_path,
        reward_formula_path,
        regressor_path,
    )
    if not all(path.exists() for path in required_paths):
        return None

    import joblib

    return ArtifactBundle(
        feature_columns=_read_json_list(feature_columns_path),
        feature_schema=_read_json_dict(feature_schema_path),
        query_mapping=_read_json_dict(query_mapping_path),
        training_metadata=_read_json_dict(training_metadata_path),
        bandit_params=_read_json_dict(bandit_params_path),
        reward_formula=_read_json_dict(reward_formula_path),
        regressor=joblib.load(regressor_path),
        source=str(artifact_dir),
    )


def get_artifact_source() -> str:
    """Return the resolved artifact source for health/reporting."""
    artifact_dir = resolve_artifact_dir()
    return str(artifact_dir) if artifact_dir is not None else "unconfigured"


@lru_cache(maxsize=1)
def resolve_artifact_dir() -> Path | None:
    """Resolve the directory containing deployable artifacts."""
    explicit_artifact_dir = os.getenv("MODEL_ARTIFACT_DIR", "").strip()
    if explicit_artifact_dir:
        artifact_dir = Path(explicit_artifact_dir).expanduser().resolve()
        return artifact_dir if artifact_dir.exists() else None

    hf_repo_id = os.getenv("HF_MODEL_REPO_ID", "").strip()
    if hf_repo_id:
        return _download_hf_snapshot(repo_id=hf_repo_id)

    return ARTIFACT_DIR if ARTIFACT_DIR.exists() else None


def _download_hf_snapshot(repo_id: str) -> Path:
    """Download model artifacts from Hugging Face Hub."""
    from huggingface_hub import snapshot_download

    revision = os.getenv("HF_MODEL_REVISION", "").strip() or None
    token = os.getenv("HF_TOKEN", "").strip() or None
    local_dir = os.getenv("HF_MODEL_CACHE_DIR", "").strip() or None

    snapshot_path = snapshot_download(
        repo_id=repo_id,
        repo_type="model",
        revision=revision,
        token=token,
        local_dir=local_dir,
        allow_patterns=[
            "feature_columns.json",
            "feature_schema.json",
            "query_mapping.json",
            "training_metadata.json",
            "bandit_params.json",
            "reward_formula.json",
            "reward_regressor.joblib",
            "README.md",
        ],
    )
    return Path(snapshot_path).resolve()


def _read_json_list(path: Path) -> list[str]:
    """Read a list[str] JSON file."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [str(item) for item in payload]


def _read_json_dict(path: Path) -> dict[str, Any]:
    """Read a dict JSON file."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {str(key): value for key, value in payload.items()}
