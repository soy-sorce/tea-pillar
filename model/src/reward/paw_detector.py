"""YOLOv8-backed paw-hit estimation."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Self


@dataclass(slots=True)
class PawDetectionResult:
    """Paw-hit extraction result."""

    paw_hit_count: int
    sampled_frames: int


class PawDetector:
    """Estimate paw-hit count from a reaction video.

    The first implementation constrains analysis to cat detections from YOLOv8
    and counts high-motion events inside those regions. It is intentionally
    heuristic but keeps the implementation aligned with MODELING.md.
    """

    def __init__(
        self: Self,
        *,
        model_name: str = "yolov8n.pt",
        frame_stride: int = 4,
        motion_threshold: float = 22.0,
    ) -> None:
        self._cv2, yolo_cls = _import_runtime_dependencies()
        self._model = yolo_cls(model_name)
        self._frame_stride = frame_stride
        self._motion_threshold = motion_threshold

    def detect(self: Self, video_path: str | Path) -> PawDetectionResult:
        """Estimate paw-hit count from a local video file."""
        capture = self._cv2.VideoCapture(str(video_path))
        if not capture.isOpened():
            raise RuntimeError(f"failed to open video: {video_path}")

        previous_region = None
        motion_events = 0
        sampled_frames = 0
        frame_index = 0

        try:
            while True:
                ok, frame = capture.read()
                if not ok:
                    break
                frame_index += 1
                if frame_index % self._frame_stride != 0:
                    continue

                region = self._extract_cat_motion_region(frame)
                if region is None:
                    previous_region = None
                    continue

                sampled_frames += 1
                gray = self._cv2.cvtColor(region, self._cv2.COLOR_BGR2GRAY)
                blurred = self._cv2.GaussianBlur(gray, (5, 5), 0)
                if previous_region is not None:
                    if previous_region.shape != blurred.shape:
                        blurred = self._cv2.resize(
                            blurred,
                            (previous_region.shape[1], previous_region.shape[0]),
                            interpolation=self._cv2.INTER_LINEAR,
                        )
                    diff = self._cv2.absdiff(previous_region, blurred)
                    score = float(diff.mean())
                    if score >= self._motion_threshold:
                        motion_events += 1
                previous_region = blurred
        finally:
            capture.release()

        paw_hit_count = max(0, motion_events // 2)
        return PawDetectionResult(paw_hit_count=paw_hit_count, sampled_frames=sampled_frames)

    def _extract_cat_motion_region(self: Self, frame: Any) -> Any | None:
        """Crop the lower half of the strongest cat detection."""
        results = self._model.predict(frame, verbose=False)
        boxes = list(_iter_cat_boxes(results))
        if not boxes:
            return None
        box = max(boxes, key=lambda item: item[2] * item[3])
        x, y, width, height = box
        lower_y = y + (height // 2)
        return frame[lower_y : y + height, x : x + width]


def _iter_cat_boxes(results: Iterable[Any]) -> Iterable[tuple[int, int, int, int]]:
    """Yield cat bounding boxes from YOLO results."""
    for result in results:
        boxes = getattr(result, "boxes", None)
        if boxes is None:
            continue
        xywh = boxes.xywh.cpu().numpy().tolist()
        classes = boxes.cls.cpu().numpy().tolist()
        for box, cls_id in zip(xywh, classes, strict=True):
            if int(cls_id) != 15:
                continue
            center_x, center_y, width, height = (int(value) for value in box)
            yield (
                max(0, center_x - width // 2),
                max(0, center_y - height // 2),
                max(1, width),
                max(1, height),
            )


def _import_runtime_dependencies() -> tuple[Any, Any]:
    """Import heavy dependencies lazily."""
    try:
        import cv2
        import ultralytics
    except ImportError as exc:
        raise RuntimeError(
            "reward analysis dependencies are missing. "
            "Install opencv-python-headless and ultralytics."
        ) from exc
    yolo_cls = ultralytics.YOLO  # type: ignore[attr-defined]
    return cv2, yolo_cls
