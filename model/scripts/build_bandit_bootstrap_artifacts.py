"""Build artifact files used by the backend/model runtime."""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from pathlib import Path

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build bootstrap artifacts from extracted tables.")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--context-features", type=Path, required=True)
    parser.add_argument("--reward-labels", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--alpha", type=float, default=0.3)
    parser.add_argument("--beta", type=float, default=0.05)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.artifact_dir.mkdir(parents=True, exist_ok=True)

    manifest_df = pd.read_csv(args.manifest)
    context_df = pd.read_csv(args.context_features)
    reward_df = pd.read_csv(args.reward_labels)

    query_ids = sorted(manifest_df["template_id"].astype(str).unique().tolist())
    feature_names = sorted(
        [
            column
            for column in context_df.columns
            if (
                column.startswith("emotion_")
                or column.startswith("clip_")
                or column.startswith("pose_")
            )
        ]
    )
    state_keys = sorted(context_df["state_key"].astype(str).unique().tolist())

    bandit_params = {
        f"{state_key}__{query_id}": {
            "state_key": state_key,
            "template_id": query_id,
            "alpha": 1.0,
            "beta": 1.0,
            "selection_count": 0,
            "reward_sum": 0.0,
        }
        for state_key in state_keys
        for query_id in query_ids
    }
    query_mapping = {query_id: {"template_id": query_id} for query_id in query_ids}
    feature_schema = {
        "feature_names": feature_names,
        "aux_label_names": ["emotion_label", "clip_top_label", "meow_label"],
        "state_key_format": "{meow_label or unknown}_{emotion_label}_{clip_top_label}",
    }
    training_metadata = {
        "version": "v2-video-reward",
        "sessions": int(len(manifest_df)),
        "context_rows": int(len(context_df)),
        "reward_rows": int(len(reward_df)),
        "templates": len(query_ids),
        "state_keys": len(state_keys),
        "reward_mean": float(reward_df["reward"].mean()) if not reward_df.empty else 0.0,
        "reward_std": float(reward_df["reward"].std(ddof=0)) if not reward_df.empty else 0.0,
    }
    reward_formula = {
        "paw_alpha": args.alpha,
        "gaze_beta": args.beta,
        "reward_formula_version": "v2-video-reward",
    }

    write_json(args.artifact_dir / "bandit_params.json", bandit_params)
    write_json(args.artifact_dir / "query_mapping.json", query_mapping)
    write_json(args.artifact_dir / "feature_schema.json", feature_schema)
    write_json(args.artifact_dir / "training_metadata.json", training_metadata)
    write_json(args.artifact_dir / "reward_formula.json", reward_formula)
    print(f"[DONE] wrote artifacts to {args.artifact_dir}")


def write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
