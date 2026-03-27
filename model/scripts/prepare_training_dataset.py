"""Normalize raw training data into a session manifest."""

from __future__ import annotations

import argparse
import csv
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Self

CONDITION_NAMES = {"飼い主あり", "飼い主なし", "飼い主撫で"}
IMAGE_CANDIDATES = {
    "before": ("before.png", "before.PNG", "before.jpg", "before.jpeg", "before.JPG"),
    "after": ("after.png", "after.PNG", "after.jpg", "after.jpeg", "after.JPG"),
}
VIDEO_SUFFIXES = (".mp4", ".mov", ".MOV")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare nekkoflix training manifest from raw data."
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="zip file or extracted train-data dir",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    with _MaterializeInput(args.input) as data_root:
        manifest_path = args.output_dir / "session_manifest.csv"
        rows = list(iter_manifest_rows(data_root))
        write_manifest(rows, manifest_path)
        print(f"[DONE] wrote {len(rows)} rows to {manifest_path}")


def iter_manifest_rows(data_root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for video_dir in sorted(
        path for path in data_root.iterdir() if path.is_dir() and path.name.startswith("video-")
    ):
        template_video_path = video_dir / "video.mp4"
        for session_dir in sorted(path for path in video_dir.iterdir() if path.is_dir()):
            if session_dir.name in CONDITION_NAMES:
                rows.extend(_rows_from_condition_dir(video_dir, session_dir, template_video_path))
                continue
            row = build_row(
                video_dir=video_dir,
                session_dir=session_dir,
                template_video_path=template_video_path,
                condition="default",
            )
            if row is not None:
                rows.append(row)
    return rows


def _rows_from_condition_dir(
    video_dir: Path,
    condition_dir: Path,
    template_video_path: Path,
) -> list[dict[str, str]]:
    grouped: dict[str, dict[str, Path]] = {}
    for child in sorted(condition_dir.iterdir()):
        if child.suffix not in VIDEO_SUFFIXES:
            continue
        stem = child.stem
        phase = "after" if "after" in stem.lower() else "before"
        cat_name = (
            stem.replace("before", "")
            .replace("after", "")
            .replace("Before", "")
            .replace("After", "")
        )
        cat_name = cat_name.replace("_", "").replace("-", "").strip() or "unknown"
        grouped.setdefault(cat_name, {})[phase] = child

    rows: list[dict[str, str]] = []
    for cat_name, phase_map in sorted(grouped.items()):
        before_video = phase_map.get("before")
        after_video = phase_map.get("after")
        if before_video is None and after_video is None:
            continue
        image_dir = video_dir / cat_name
        before_image = find_existing(image_dir, IMAGE_CANDIDATES["before"])
        after_image = find_existing(image_dir, IMAGE_CANDIDATES["after"])
        rows.append(
            {
                "session_id": f"{video_dir.name}__{condition_dir.name}__{cat_name}",
                "template_id": video_dir.name,
                "cat_name": cat_name,
                "condition": condition_dir.name,
                "before_image_path": str(before_image) if before_image is not None else "",
                "after_image_path": str(after_image) if after_image is not None else "",
                "before_video_path": str(before_video) if before_video is not None else "",
                "after_video_path": str(after_video) if after_video is not None else "",
                "reaction_video_path": str(after_video) if after_video is not None else "",
                "template_video_path": (
                    str(template_video_path) if template_video_path.exists() else ""
                ),
            }
        )
    return rows


def build_row(
    *,
    video_dir: Path,
    session_dir: Path,
    template_video_path: Path,
    condition: str,
) -> dict[str, str] | None:
    before_image = find_existing(session_dir, IMAGE_CANDIDATES["before"])
    after_image = find_existing(session_dir, IMAGE_CANDIDATES["after"])
    before_video = find_phase_video(session_dir, "before")
    after_video = find_phase_video(session_dir, "after")
    if (
        before_image is None
        and after_image is None
        and before_video is None
        and after_video is None
    ):
        return None
    return {
        "session_id": f"{video_dir.name}__{condition}__{session_dir.name}",
        "template_id": video_dir.name,
        "cat_name": session_dir.name,
        "condition": condition,
        "before_image_path": str(before_image) if before_image is not None else "",
        "after_image_path": str(after_image) if after_image is not None else "",
        "before_video_path": str(before_video) if before_video is not None else "",
        "after_video_path": str(after_video) if after_video is not None else "",
        "reaction_video_path": str(after_video) if after_video is not None else "",
        "template_video_path": str(template_video_path) if template_video_path.exists() else "",
    }


def find_existing(directory: Path, candidates: tuple[str, ...]) -> Path | None:
    for candidate in candidates:
        path = directory / candidate
        if path.exists():
            return path
    return None


def find_phase_video(directory: Path, phase: str) -> Path | None:
    candidates = sorted(
        path
        for path in directory.iterdir()
        if path.is_file() and path.suffix in VIDEO_SUFFIXES and phase.lower() in path.stem.lower()
    )
    return candidates[0] if candidates else None


def write_manifest(rows: list[dict[str, str]], destination: Path) -> None:
    fieldnames = [
        "session_id",
        "template_id",
        "cat_name",
        "condition",
        "before_image_path",
        "after_image_path",
        "before_video_path",
        "after_video_path",
        "reaction_video_path",
        "template_video_path",
    ]
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


class _MaterializeInput:
    def __init__(self: Self, input_path: Path) -> None:
        self._input_path = input_path
        self._temp_dir: Path | None = None

    def __enter__(self: Self) -> Path:
        if self._input_path.is_dir():
            return self._input_path
        if self._input_path.suffix != ".zip":
            raise SystemExit(f"unsupported input: {self._input_path}")
        temp_dir = Path(tempfile.mkdtemp(prefix="nekkoflix-train-data-"))
        with zipfile.ZipFile(self._input_path) as archive:
            archive.extractall(temp_dir)
        self._temp_dir = temp_dir
        extracted_root = temp_dir / "train-data"
        if not extracted_root.exists():
            raise SystemExit("zip does not contain train-data/")
        return extracted_root

    def __exit__(
        self: Self,
        exc_type: object,
        exc: object,
        traceback: object,
    ) -> None:
        del exc_type, exc, traceback
        if self._temp_dir is not None and self._temp_dir.exists():
            shutil.rmtree(self._temp_dir)
