"""Extract context features from normalized session manifest."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from importlib import import_module
from pathlib import Path

import pandas as pd

MODEL_DIR = Path(__file__).resolve().parents[1]
if str(MODEL_DIR) not in sys.path:
    sys.path.insert(0, str(MODEL_DIR))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract context features from before images.")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", type=str, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = []
    feature_extractor_module = import_module("src.feature_extractor")
    feature_extractor_cls = feature_extractor_module.FeatureExtractor
    extractor = feature_extractor_cls(device=args.device)
    with args.manifest.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for record in reader:
            before_image_path = record["before_image_path"].strip()
            if not before_image_path:
                continue
            features, aux_labels = extractor.extract_image_path(before_image_path)
            rows.append(
                {
                    "session_id": record["session_id"],
                    "template_id": record["template_id"],
                    "cat_name": record["cat_name"],
                    "condition": record["condition"],
                    "state_key": build_state_key(aux_labels),
                    "features_json": json.dumps(features, ensure_ascii=False, sort_keys=True),
                    "aux_labels_json": json.dumps(aux_labels, ensure_ascii=False, sort_keys=True),
                    **features,
                    **{key: value for key, value in aux_labels.items()},
                }
            )
    df = pd.DataFrame(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False)
    print(f"[DONE] wrote {len(df)} context rows to {args.output}")


def build_state_key(aux_labels: dict[str, str | None]) -> str:
    meow = aux_labels.get("meow_label") or "unknown"
    emotion = aux_labels.get("emotion_label") or "unknown"
    clip_top = aux_labels.get("clip_top_label") or "unknown"
    return f"{meow}_{emotion}_{clip_top}"


if __name__ == "__main__":
    main()
