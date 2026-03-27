"""Upload the model artifact bundle to a Hugging Face model repository."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv
from huggingface_hub import HfApi

DEFAULT_ARTIFACT_DIR = Path(__file__).resolve().parents[1] / "artifacts"


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Publish nekkoflix model artifacts to Hugging Face Hub.",
    )
    parser.add_argument(
        "--repo-id",
        required=True,
        help="Hugging Face model repo id, e.g. org/name",
    )
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--revision", default="main")
    parser.add_argument("--private", action="store_true")
    parser.add_argument(
        "--commit-message",
        default="Upload nekkoflix MODELING.md v2 artifact bundle",
    )
    return parser.parse_args()


def main() -> None:
    """Create/update a model repo and upload the artifact directory."""
    args = parse_args()
    load_dotenv()
    token = os.getenv("HF_TOKEN", "").strip()
    if not token:
        raise SystemExit("HF_TOKEN is required")
    if not args.artifact_dir.exists():
        raise SystemExit(f"artifact dir does not exist: {args.artifact_dir}")

    api = HfApi(token=token)
    api.create_repo(
        repo_id=args.repo_id,
        repo_type="model",
        private=args.private,
        exist_ok=True,
    )
    api.upload_folder(
        repo_id=args.repo_id,
        repo_type="model",
        folder_path=str(args.artifact_dir),
        revision=args.revision,
        commit_message=args.commit_message,
    )
    print(f"[DONE] uploaded {args.artifact_dir} to https://huggingface.co/{args.repo_id}")


if __name__ == "__main__":
    main()
