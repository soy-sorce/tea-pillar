"""MediaPipe-backed gaze-duration estimation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Self


@dataclass(slots=True)
class GazeEstimationResult:
    """Gaze estimation result."""

    gaze_duration_seconds: float
    sampled_frames: int


class GazeEstimator:
    """Estimate how long the cat faces the screen.

    This implementation uses MediaPipe detections as a pragmatic proxy:
    if a face is detected near the screen-facing region, the frame counts as
    attentive. It is intentionally lightweight for the hackathon dataset.
    """

    def __init__(
        self: Self,
        *,
        frame_stride: int = 3,
        attention_margin_ratio: float = 0.2,
        yolo_model_name: str = "yolov8n.pt",
    ) -> None:
        cv2, mp, yolo_cls = _import_runtime_dependencies()
        self._cv2 = cv2
        self._mode = "mediapipe" if hasattr(mp, "solutions") else "yolo_proxy"
        self._mp_face_detection = None
        self._yolo_model = None
        if self._mode == "mediapipe":
            self._mp_face_detection = mp.solutions.face_detection.FaceDetection(
                model_selection=0,
                min_detection_confidence=0.5,
            )
        else:
            self._yolo_model = yolo_cls(yolo_model_name)
        self._frame_stride = frame_stride
        self._attention_margin_ratio = attention_margin_ratio

    def estimate(self: Self, video_path: str | Path) -> GazeEstimationResult:
        """Estimate attentive duration from a local video file."""
        capture = self._cv2.VideoCapture(str(video_path))
        if not capture.isOpened():
            raise RuntimeError(f"failed to open video: {video_path}")

        fps = capture.get(self._cv2.CAP_PROP_FPS) or 30.0
        attentive_frames = 0
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

                sampled_frames += 1
                if self._is_screen_facing(frame):
                    attentive_frames += 1
        finally:
            capture.release()

        seconds = attentive_frames * (self._frame_stride / fps)
        return GazeEstimationResult(
            gaze_duration_seconds=round(float(seconds), 3),
            sampled_frames=sampled_frames,
        )

    def _is_screen_facing(self: Self, frame: Any) -> bool:
        """Treat central face detections as screen-facing."""
        if self._mode == "yolo_proxy":
            return self._is_screen_facing_yolo(frame)
        rgb = self._cv2.cvtColor(frame, self._cv2.COLOR_BGR2RGB)
        assert self._mp_face_detection is not None
        result = self._mp_face_detection.process(rgb)
        detections = getattr(result, "detections", None) or []
        if not detections:
            return False

        height, width, _ = frame.shape
        margin_x = width * self._attention_margin_ratio
        margin_y = height * self._attention_margin_ratio
        for detection in detections:
            box = detection.location_data.relative_bounding_box
            center_x = (box.xmin + box.width / 2.0) * width
            center_y = (box.ymin + box.height / 2.0) * height
            if margin_x <= center_x <= (width - margin_x) and margin_y <= center_y <= (
                height - margin_y
            ):
                return True
        return False

    def _is_screen_facing_yolo(self: Self, frame: Any) -> bool:
        """Fallback gaze proxy when MediaPipe FaceDetection is unavailable.

        We treat a cat detection near the center of the frame as 'watching the
        screen'. This is weaker than face-direction estimation but keeps the
        video reward pipeline usable with modern mediapipe packages that no
        longer expose `solutions` at the top level.
        """
        assert self._yolo_model is not None
        results = self._yolo_model.predict(frame, verbose=False)
        height, width, _ = frame.shape
        margin_x = width * self._attention_margin_ratio
        margin_y = height * self._attention_margin_ratio
        for result in results:
            boxes = getattr(result, "boxes", None)
            if boxes is None:
                continue
            xywh = boxes.xywh.cpu().numpy().tolist()
            classes = boxes.cls.cpu().numpy().tolist()
            for box, cls_id in zip(xywh, classes, strict=True):
                if int(cls_id) != 15:
                    continue
                center_x, center_y, _, _ = (float(value) for value in box)
                if margin_x <= center_x <= (width - margin_x) and margin_y <= center_y <= (
                    height - margin_y
                ):
                    return True
        return False


def _import_runtime_dependencies() -> tuple[Any, Any, Any]:
    """Import heavy dependencies lazily."""
    try:
        import cv2
        import mediapipe as mp
        import ultralytics
    except ImportError as exc:
        raise RuntimeError(
            "reward analysis dependencies are missing. "
            "Install opencv-python-headless, mediapipe, and ultralytics."
        ) from exc
    yolo_cls = ultralytics.YOLO  # type: ignore[attr-defined]
    return cv2, mp, yolo_cls
