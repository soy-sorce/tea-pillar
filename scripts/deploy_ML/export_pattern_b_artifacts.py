"""Export model artifacts from pattern_b session features.

This script bridges `tea-pillar-ML-analysis` outputs into the `tea-pillar/model`
artifact bundle expected by the custom predictor.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import joblib
import lightgbm as lgb
import pandas as pd
from sklearn.preprocessing import OneHotEncoder

DEFAULT_SESSION_FEATURE_TABLE = Path(
    "/home/shouh/team_project/GCP_hackathon_2026/"
    "tea-pillar-ML-analysis/script/v1/modeling/script/output/pattern_b/session_feature_table.csv"
)
DEFAULT_ARTIFACT_DIR = Path(
    "/home/shouh/team_project/GCP_hackathon_2026/tea-pillar/model/artifacts"
)
DEFAULT_CLIP_PROMPTS = {
    "clip_attentive_cat": "attentive cat",
    "clip_relaxed_cat": "relaxed cat",
    "clip_stressed_cat": "stressed cat",
    "clip_playful_cat": "playful cat",
    "clip_sleepy_cat": "sleepy cat",
    "clip_curious_cat": "curious cat",
    "clip_alert_cat": "alert cat",
    "clip_comfortable_cat": "comfortable cat",
}


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Export v1 pattern_b artifacts into tea-pillar/model/artifacts.",
    )
    parser.add_argument(
        "--session-feature-table",
        type=Path,
        default=DEFAULT_SESSION_FEATURE_TABLE,
        help="pattern_b session_feature_table.csv path",
    )
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=DEFAULT_ARTIFACT_DIR,
        help="Output artifact directory",
    )
    return parser.parse_args()


def main() -> None:
    """Train the regressor and export deployable artifacts."""
    args = parse_args()
    df = pd.read_csv(args.session_feature_table)
    artifact_dir = args.artifact_dir
    artifact_dir.mkdir(parents=True, exist_ok=True)

    before_feature_columns = _get_before_feature_columns(df)
    encoder = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
    video_onehot = encoder.fit_transform(df[["video_id"]])
    video_ids = [str(video_id) for video_id in encoder.categories_[0]]
    video_feature_columns = [f"video_{video_id}" for video_id in video_ids]

    x = pd.concat(
        [
            df[before_feature_columns].reset_index(drop=True),
            pd.DataFrame(video_onehot, columns=video_feature_columns),
        ],
        axis=1,
    )
    y = df["reward"]

    regressor = lgb.LGBMRegressor(
        objective="regression",
        n_estimators=300,
        learning_rate=0.03,
        num_leaves=7,
        min_data_in_leaf=1,
        min_data_in_bin=1,
        max_depth=3,
        verbosity=-1,
        random_state=42,
    )
    regressor.fit(x, y)

    feature_columns = x.columns.tolist()
    training_metadata = _build_training_metadata(df=df, video_ids=video_ids)

    joblib.dump(regressor, artifact_dir / "reward_regressor.joblib")
    _write_json(artifact_dir / "feature_columns.json", feature_columns)
    _write_json(artifact_dir / "video_id_mapping.json", video_ids)
    _write_json(artifact_dir / "training_metadata.json", training_metadata)
    _write_json(artifact_dir / "clip_prompts.json", DEFAULT_CLIP_PROMPTS)

    print("[DONE] Exported artifacts:")
    print(f"  - {artifact_dir / 'reward_regressor.joblib'}")
    print(f"  - {artifact_dir / 'feature_columns.json'}")
    print(f"  - {artifact_dir / 'video_id_mapping.json'}")
    print(f"  - {artifact_dir / 'training_metadata.json'}")
    print(f"  - {artifact_dir / 'clip_prompts.json'}")


def _get_before_feature_columns(df: pd.DataFrame) -> list[str]:
    """Return numeric before_* feature columns."""
    return [
        column
        for column in df.columns
        if column.startswith("before_") and pd.api.types.is_numeric_dtype(df[column])
    ]


def _build_training_metadata(df: pd.DataFrame, video_ids: list[str]) -> dict[str, Any]:
    """Build deployment metadata for the exported bundle."""
    return {
        "version": "v1",
        "emotion_model_id": "semihdervis/cat-emotion-classifier",
        "pose_model_id": "usyd-community/vitpose-plus-small",
        "clip_model_id": "openai/clip-vit-base-patch32",
        "audio_model_id": "IsolaHGVIS/Cat-Meow-Classification",
        "regressor_type": "lightgbm_regressor",
        "candidate_video_count": len(video_ids),
        "reward_formula_version": "reward_v1",
        "training_rows": int(len(df)),
        "cats": int(df["cat_name"].nunique()),
        "videos": int(df["video_id"].nunique()),
        "reward_mean": float(df["reward"].mean()),
        "reward_std": float(df["reward"].std(ddof=0)),
    }


def _write_json(path: Path, payload: Any) -> None:
    """Write JSON with UTF-8 and indentation."""
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
