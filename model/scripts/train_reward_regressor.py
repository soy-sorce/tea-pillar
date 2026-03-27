"""Train reward regressor from the regression training table."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import lightgbm as lgb
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train reward regressor.")
    parser.add_argument("--training-table", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.artifact_dir.mkdir(parents=True, exist_ok=True)
    print(f"[START] loading regression table from {args.training_table}")
    df = pd.read_csv(args.training_table)
    print(f"[INFO] loaded {len(df)} training rows")

    numeric_feature_columns = [
        column
        for column in df.columns
        if (
            column.startswith("emotion_")
            or column.startswith("clip_")
            or column.startswith("pose_")
        )
        and pd.api.types.is_numeric_dtype(df[column])
    ]
    dropped_prefixed_columns = [
        column
        for column in df.columns
        if (
            column.startswith("emotion_")
            or column.startswith("clip_")
            or column.startswith("pose_")
        )
        and column not in numeric_feature_columns
    ]
    video_frame = pd.get_dummies(df["template_id"].astype(str), prefix="video", dtype=float)
    x = pd.concat(
        [df[numeric_feature_columns].reset_index(drop=True), video_frame.reset_index(drop=True)],
        axis=1,
    )
    y = df["reward"].astype(float)
    print(
        "[INFO] prepared regression matrix",
        f"base_features={len(numeric_feature_columns)}",
        f"video_features={len(video_frame.columns)}",
        f"total_features={len(x.columns)}",
    )
    if dropped_prefixed_columns:
        print(
            f"[INFO] excluded non-numeric prefixed columns: {', '.join(dropped_prefixed_columns)}"
        )

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
    print("[START] training LightGBM reward regressor")
    regressor.fit(x, y)
    print("[DONE] trained LightGBM reward regressor")

    joblib.dump(regressor, args.artifact_dir / "reward_regressor.joblib")
    (args.artifact_dir / "feature_columns.json").write_text(
        json.dumps(x.columns.tolist(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[DONE] wrote regressor to {args.artifact_dir / 'reward_regressor.joblib'}")
    print(f"[DONE] wrote feature columns to {args.artifact_dir / 'feature_columns.json'}")


if __name__ == "__main__":
    main()
