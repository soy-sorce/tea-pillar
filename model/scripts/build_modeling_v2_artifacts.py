"""End-to-end artifact builder aligned with MODELING.md."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import zipfile
from importlib import import_module
from pathlib import Path

MODEL_DIR = Path(__file__).resolve().parents[1]
if str(MODEL_DIR) not in sys.path:
    sys.path.insert(0, str(MODEL_DIR))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build MODELING.md v2 artifacts from raw train data."
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="zip file or extracted train-data dir",
    )
    parser.add_argument("--work-dir", type=Path, default=MODEL_DIR / "training_output" / "v2")
    parser.add_argument("--artifact-dir", type=Path, default=MODEL_DIR / "artifacts")
    return parser.parse_args()


def main() -> None:
    prepare_dataset = import_module("scripts.prepare_training_dataset")
    iter_manifest_rows = prepare_dataset.iter_manifest_rows
    write_manifest = prepare_dataset.write_manifest

    args = parse_args()
    args.work_dir.mkdir(parents=True, exist_ok=True)
    print(f"[START] build_modeling_v2_artifacts input={args.input}")
    data_root = materialize_training_input(args.input, args.work_dir)
    print(f"[INFO] normalized training root={data_root}")
    manifest_path = args.work_dir / "session_manifest.csv"
    context_path = args.work_dir / "context_features.csv"
    reward_path = args.work_dir / "reward_labels.csv"
    training_table_path = args.work_dir / "regression_training_table.csv"

    write_manifest(iter_manifest_rows(data_root), manifest_path)
    print(f"[DONE] wrote manifest to {manifest_path}")
    run_script(
        "extract_context_features.py",
        "--manifest",
        str(manifest_path),
        "--output",
        str(context_path),
    )
    run_script(
        "extract_reward_labels.py",
        "--manifest",
        str(manifest_path),
        "--output",
        str(reward_path),
    )
    run_script(
        "build_regression_training_table.py",
        "--context-features",
        str(context_path),
        "--reward-labels",
        str(reward_path),
        "--output",
        str(training_table_path),
    )
    run_script(
        "train_reward_regressor.py",
        "--training-table",
        str(training_table_path),
        "--artifact-dir",
        str(args.artifact_dir),
    )
    print(f"[DONE] artifacts available under {args.artifact_dir}")
    run_script(
        "build_bandit_bootstrap_artifacts.py",
        "--manifest",
        str(manifest_path),
        "--context-features",
        str(context_path),
        "--reward-labels",
        str(reward_path),
        "--artifact-dir",
        str(args.artifact_dir),
    )


def run_script(script_name: str, *args: str) -> None:
    cmd = [sys.executable, str(MODEL_DIR / "scripts" / script_name), *args]
    print(f"[RUN] {script_name} {' '.join(args)}")
    subprocess.run(cmd, cwd=MODEL_DIR, check=True)
    print(f"[DONE] {script_name}")


def materialize_training_input(input_path: Path, work_dir: Path) -> Path:
    """Resolve training data into a stable on-disk directory for child scripts."""
    if input_path.is_dir():
        return input_path.resolve()
    if input_path.suffix != ".zip":
        raise SystemExit(f"unsupported input: {input_path}")

    extracted_root = work_dir / "raw_train_data"
    if extracted_root.exists():
        shutil.rmtree(extracted_root)
    extracted_root.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(input_path) as archive:
        archive.extractall(extracted_root)

    train_data_root = extracted_root / "train-data"
    if not train_data_root.exists():
        raise SystemExit("zip does not contain train-data/")
    return train_data_root.resolve()


if __name__ == "__main__":
    main()
