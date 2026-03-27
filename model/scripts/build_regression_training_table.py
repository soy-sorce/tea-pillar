"""Build a regression training table from extracted context and reward labels."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build reward regressor training table.")
    parser.add_argument("--context-features", type=Path, required=True)
    parser.add_argument("--reward-labels", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    context_df = pd.read_csv(args.context_features)
    reward_df = pd.read_csv(args.reward_labels)

    training_df = context_df.merge(
        reward_df[["session_id", "reward"]],
        on="session_id",
        how="inner",
        validate="one_to_one",
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    training_df.to_csv(args.output, index=False)
    print(f"[DONE] wrote {len(training_df)} rows to {args.output}")


if __name__ == "__main__":
    main()
