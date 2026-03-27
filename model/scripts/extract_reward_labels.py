"""Extract video-based reward labels from normalized session manifest."""

from __future__ import annotations

import argparse
import csv
import sys
from importlib import import_module
from pathlib import Path

import pandas as pd

MODEL_DIR = Path(__file__).resolve().parents[1]
if str(MODEL_DIR) not in sys.path:
    sys.path.insert(0, str(MODEL_DIR))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract reward labels from reaction videos.")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--paw-alpha", type=float, default=0.3)
    parser.add_argument("--gaze-beta", type=float, default=0.05)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paw_detector_module = import_module("src.reward.paw_detector")
    gaze_estimator_module = import_module("src.reward.gaze_estimator")
    paw_detector = paw_detector_module.PawDetector()
    gaze_estimator = gaze_estimator_module.GazeEstimator()
    rows = []
    with args.manifest.open("r", encoding="utf-8", newline="") as handle:
        manifest_rows = list(csv.DictReader(handle))
        total = len(manifest_rows)
        print(f"[START] extracting reward labels from {total} manifest rows")
        for index, record in enumerate(manifest_rows, start=1):
            reaction_video_path = record["reaction_video_path"].strip()
            if not reaction_video_path:
                print(
                    f"[SKIP] {index}/{total} "
                    f"session_id={record['session_id']} "
                    "reaction_video_path is empty"
                )
                continue
            print(
                f"[RUN] {index}/{total} session_id={record['session_id']} "
                f"template_id={record['template_id']} video={reaction_video_path}"
            )
            paw = paw_detector.detect(reaction_video_path)
            gaze = gaze_estimator.estimate(reaction_video_path)
            reward = round(
                (args.paw_alpha * paw.paw_hit_count)
                + (args.gaze_beta * gaze.gaze_duration_seconds),
                6,
            )
            rows.append(
                {
                    "session_id": record["session_id"],
                    "template_id": record["template_id"],
                    "cat_name": record["cat_name"],
                    "condition": record["condition"],
                    "reaction_video_path": reaction_video_path,
                    "paw_hit_count": paw.paw_hit_count,
                    "gaze_duration_seconds": gaze.gaze_duration_seconds,
                    "reward": reward,
                    "reward_formula_version": "v2-video-reward",
                }
            )
            print(
                f"[DONE] {index}/{total} session_id={record['session_id']} "
                f"paw_hit_count={paw.paw_hit_count} "
                f"gaze_duration_seconds={gaze.gaze_duration_seconds:.4f} "
                f"reward={reward:.6f}"
            )
    df = pd.DataFrame(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False)
    print(f"[DONE] wrote {len(df)} reward rows to {args.output}")


if __name__ == "__main__":
    main()
