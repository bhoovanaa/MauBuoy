"""Computer-vision inference for ReefGuardian AI.

The deployable health model is the supplied three-class YOLO11n detector.
The supplied ``vit_b_coralscop.pth`` checkpoint is a Segment Anything ViT-B
state dict, so it is used only as an optional box-prompted segmentation
refinement. It does not vote on Healthy/Bleached/Dead.

Models are loaded lazily. This keeps the API responsive for environmental-only
requests and produces a useful error when heavyweight CV dependencies have not
yet been installed.
"""

from __future__ import annotations

import base64
import math
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Any, Iterable


BASE_DIR = Path(__file__).resolve().parent
try:
    from dotenv import load_dotenv

    load_dotenv(BASE_DIR.parent / ".env")
except ImportError:
    pass

_configured_model_dir = Path(
    os.getenv("REEFGUARDIAN_MODEL_DIR", str(BASE_DIR / "models"))
)
MODEL_DIR = (
    _configured_model_dir
    if _configured_model_dir.is_absolute()
    else BASE_DIR.parent / _configured_model_dir
)
DEFAULT_YOLO_PATH = MODEL_DIR / "reefguardian_yolo11n_best.pt"
DEFAULT_SAM_PATH = MODEL_DIR / "vit_b_coralscop.pth"


class ModelUnavailableError(RuntimeError):
    """Raised when an inference model or its runtime cannot be loaded."""


@dataclass(frozen=True)
class VisionConfig:
    """Reliability thresholds recorded in the development report."""

    min_confidence: float = 0.50
    inference_confidence: float = 0.25
    min_area_ratio: float = 0.015
    max_area_ratio: float = 0.80
    min_sharpness: float = 25.0
    target_area_ratio: float = 0.25
    max_closeups: int = 3
    image_size: int = 640
    nms_iou: float = 0.50
    video_target_fps: float = 1.0
    max_video_frames: int = 240
    duplicate_hash_distance: int = 8


def _canonical_health(label: str) -> str:
    normalized = label.strip().lower()
    return {
        "healthy": "Healthy",
        "bleached": "Bleached",
        "dead": "Dead",
    }.get(normalized, label.strip().title())


def _condition_summary(detections: Iterable[dict[str, Any]]) -> dict[str, Any]:
    votes: dict[str, float] = {}
    confidence_totals: dict[str, float] = {}
    counts: dict[str, int] = {}

    for detection in detections:
        health = detection["health"]
        confidence = float(detection["confidence"])
        quality = float(detection["quality_score"])
        weight = max(confidence * quality, 1e-9)
        votes[health] = votes.get(health, 0.0) + weight
        confidence_totals[health] = confidence_totals.get(health, 0.0) + confidence
        counts[health] = counts.get(health, 0) + 1

    if not votes:
        return {
            "overall_condition": "Uncertain",
            "confidence": 0.0,
            "class_support": {},
        }

    total = sum(votes.values())
    winner = max(votes, key=lambda label: votes[label])
    support = {label: round(weight / total, 4) for label, weight in votes.items()}
    mean_confidence = confidence_totals[winner] / counts[winner]
    return {
        "overall_condition": winner,
        "confidence": round(mean_confidence, 4),
        "class_support": support,
    }


class CoralVisionService:
    """Lazy YOLO detector plus optional SAM ViT-B segmentation refinement."""

    def __init__(
        self,
        yolo_path: str | Path | None = None,
        sam_path: str | Path | None = None,
        config: VisionConfig | None = None,
    ) -> None:
        configured_yolo = Path(
            yolo_path
            or os.getenv("REEFGUARDIAN_YOLO_MODEL", str(DEFAULT_YOLO_PATH))
        )
        configured_sam = Path(
            sam_path
            or os.getenv("REEFGUARDIAN_SAM_MODEL", str(DEFAULT_SAM_PATH))
        )
        self.yolo_path = (
            configured_yolo
            if configured_yolo.is_absolute()
            else BASE_DIR.parent / configured_yolo
        )
        self.sam_path = (
            configured_sam
            if configured_sam.is_absolute()
            else BASE_DIR.parent / configured_sam
        )
        self.config = config or VisionConfig()
        self._yolo: Any = None
        self._sam_predictor: Any = None
        self._yolo_lock = Lock()
        self._sam_lock = Lock()

    def model_status(self) -> dict[str, Any]:
        return {
            "yolo": {
                "path": str(self.yolo_path),
                "available": self.yolo_path.is_file(),
                "loaded": self._yolo is not None,
                "role": "coral detection and Healthy/Bleached/Dead classification",
            },
            "sam_vit_b": {
                "path": str(self.sam_path),
                "available": self.sam_path.is_file(),
                "loaded": self._sam_predictor is not None,
                "role": "optional YOLO-box segmentation refinement; not health classification",
            },
        }

    @staticmethod
    def _cv_runtime() -> tuple[Any, Any]:
        try:
            import cv2
            import numpy as np
        except ImportError as exc:
            raise ModelUnavailableError(
                "OpenCV/NumPy are unavailable. Install the project requirements."
            ) from exc
        return cv2, np

    def _load_yolo(self) -> Any:
        if self._yolo is not None:
            return self._yolo
        if not self.yolo_path.is_file():
            raise ModelUnavailableError(f"YOLO checkpoint not found: {self.yolo_path}")

        with self._yolo_lock:
            if self._yolo is None:
                try:
                    from ultralytics import YOLO
                except ImportError as exc:
                    raise ModelUnavailableError(
                        "Ultralytics is unavailable. Install the project requirements."
                    ) from exc
                try:
                    self._yolo = YOLO(str(self.yolo_path))
                except Exception as exc:
                    raise ModelUnavailableError(
                        f"Could not load YOLO checkpoint {self.yolo_path}: {exc}"
                    ) from exc
        return self._yolo

    def _load_sam_predictor(self) -> Any:
        if self._sam_predictor is not None:
            return self._sam_predictor
        if not self.sam_path.is_file():
            raise ModelUnavailableError(f"SAM checkpoint not found: {self.sam_path}")

        with self._sam_lock:
            if self._sam_predictor is None:
                try:
                    import torch
                    from segment_anything import SamPredictor, sam_model_registry
                except ImportError as exc:
                    raise ModelUnavailableError(
                        "Segment Anything/PyTorch are unavailable. "
                        "Install the project requirements."
                    ) from exc
                try:
                    device = os.getenv(
                        "REEFGUARDIAN_DEVICE",
                        "cuda" if torch.cuda.is_available() else "cpu",
                    )
                    sam = sam_model_registry["vit_b"](checkpoint=str(self.sam_path))
                    sam.to(device=device)
                    sam.eval()
                    self._sam_predictor = SamPredictor(sam)
                except Exception as exc:
                    raise ModelUnavailableError(
                        f"Could not load SAM ViT-B checkpoint {self.sam_path}: {exc}"
                    ) from exc
        return self._sam_predictor

    @staticmethod
    def _decode_image(image_bytes: bytes) -> Any:
        cv2, np = CoralVisionService._cv_runtime()
        array = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(array, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("The uploaded file is not a readable image.")
        return image

    @staticmethod
    def _encode_jpeg(image: Any, quality: int = 88) -> str:
        cv2, _ = CoralVisionService._cv_runtime()
        ok, encoded = cv2.imencode(
            ".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        )
        if not ok:
            raise ValueError("Could not encode image artifact.")
        return base64.b64encode(encoded.tobytes()).decode("ascii")

    @staticmethod
    def _encode_mask(mask: Any) -> str:
        cv2, np = CoralVisionService._cv_runtime()
        png_mask = (mask.astype(np.uint8) * 255)
        ok, encoded = cv2.imencode(".png", png_mask)
        if not ok:
            raise ValueError("Could not encode segmentation mask.")
        return base64.b64encode(encoded.tobytes()).decode("ascii")

    @staticmethod
    def _difference_hash(crop: Any) -> int:
        cv2, _ = CoralVisionService._cv_runtime()
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, (9, 8), interpolation=cv2.INTER_AREA)
        differences = resized[:, 1:] > resized[:, :-1]
        value = 0
        for bit in differences.flatten():
            value = (value << 1) | int(bit)
        return value

    @staticmethod
    def _hash_distance(first: int, second: int) -> int:
        return (first ^ second).bit_count()

    @staticmethod
    def _public_detection(detection: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in detection.items() if not key.startswith("_")}

    def _quality_metrics(
        self,
        image: Any,
        bbox: tuple[int, int, int, int],
        confidence: float,
    ) -> tuple[float, float, float, float]:
        cv2, _ = self._cv_runtime()
        height, width = image.shape[:2]
        x1, y1, x2, y2 = bbox
        crop = image[y1:y2, x1:x2]
        area_ratio = ((x2 - x1) * (y2 - y1)) / float(width * height)
        sharpness = 0.0
        if crop.size:
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())

        edge_clearance = min(
            x1 / width,
            y1 / height,
            (width - x2) / width,
            (height - y2) / height,
        )
        area_quality = math.exp(
            -abs(math.log(max(area_ratio, 1e-9) / self.config.target_area_ratio))
        )
        sharpness_quality = min(
            math.log1p(max(sharpness, 0.0)) / math.log1p(1500.0), 1.0
        )
        edge_quality = min(max(edge_clearance, 0.0) / 0.05, 1.0)
        quality_score = (
            0.65 * confidence
            + 0.20 * area_quality
            + 0.10 * sharpness_quality
            + 0.05 * edge_quality
        )
        return area_ratio, sharpness, edge_clearance, quality_score

    def _segment_detections(
        self,
        image: Any,
        detections: list[dict[str, Any]],
        include_artifacts: bool,
    ) -> None:
        if not detections:
            return
        cv2, np = self._cv_runtime()
        predictor = self._load_sam_predictor()
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        with self._sam_lock:
            predictor.set_image(rgb)
            for detection in detections:
                box = np.asarray(detection["bbox_xyxy"], dtype=np.float32)
                masks, scores, _ = predictor.predict(
                    point_coords=None,
                    point_labels=None,
                    box=box,
                    multimask_output=True,
                )
                best_index = int(np.argmax(scores))
                mask = masks[best_index]
                detection["segmentation"] = {
                    "model": "CoralSCOP SAM ViT-B",
                    "score": round(float(scores[best_index]), 4),
                    "image_coverage_ratio": round(float(mask.mean()), 4),
                }
                if include_artifacts:
                    detection["segmentation"]["mask_png_base64"] = self._encode_mask(
                        mask
                    )

    def _analyze_image_array(
        self,
        image: Any,
        source_id: str,
        refine_masks: bool,
        include_artifacts: bool,
    ) -> dict[str, Any]:
        cv2, _ = self._cv_runtime()
        model = self._load_yolo()
        height, width = image.shape[:2]

        with self._yolo_lock:
            results = model.predict(
                source=image,
                imgsz=self.config.image_size,
                conf=self.config.inference_confidence,
                iou=self.config.nms_iou,
                verbose=False,
            )

        result = results[0]
        names = result.names
        detections: list[dict[str, Any]] = []
        boxes = result.boxes

        if boxes is not None:
            xyxy_values = boxes.xyxy.detach().cpu().tolist()
            confidence_values = boxes.conf.detach().cpu().tolist()
            class_values = boxes.cls.detach().cpu().tolist()

            for index, (coords, confidence, class_id) in enumerate(
                zip(xyxy_values, confidence_values, class_values)
            ):
                x1 = max(0, min(width - 1, int(round(coords[0]))))
                y1 = max(0, min(height - 1, int(round(coords[1]))))
                x2 = max(x1 + 1, min(width, int(round(coords[2]))))
                y2 = max(y1 + 1, min(height, int(round(coords[3]))))
                bbox = (x1, y1, x2, y2)
                confidence = float(confidence)
                area_ratio, sharpness, edge_clearance, quality_score = (
                    self._quality_metrics(image, bbox, confidence)
                )

                rejection_reasons: list[str] = []
                if confidence < self.config.min_confidence:
                    rejection_reasons.append("confidence_below_0.50")
                if area_ratio < self.config.min_area_ratio:
                    rejection_reasons.append("box_too_small")
                if area_ratio > self.config.max_area_ratio:
                    rejection_reasons.append("box_too_large")
                if sharpness < self.config.min_sharpness:
                    rejection_reasons.append("crop_too_blurry")

                numeric_class = int(class_id)
                raw_label = (
                    names[numeric_class]
                    if isinstance(names, dict)
                    else names[numeric_class]
                )
                crop = image[y1:y2, x1:x2].copy()
                detections.append(
                    {
                        "detection_id": f"{source_id}:{index}",
                        "source_id": source_id,
                        "health": _canonical_health(str(raw_label)),
                        "class_id": numeric_class,
                        "confidence": round(confidence, 4),
                        "bbox_xyxy": [x1, y1, x2, y2],
                        "area_ratio": round(area_ratio, 4),
                        "sharpness": round(sharpness, 2),
                        "edge_clearance": round(edge_clearance, 4),
                        "quality_score": round(quality_score, 4),
                        "accepted": not rejection_reasons,
                        "rejection_reasons": rejection_reasons,
                        "_crop_bgr": crop,
                        "_crop_hash": self._difference_hash(crop),
                    }
                )

        accepted = sorted(
            (item for item in detections if item["accepted"]),
            key=lambda item: item["quality_score"],
            reverse=True,
        )
        selected = accepted[: self.config.max_closeups]

        if refine_masks:
            self._segment_detections(image, selected, include_artifacts)

        if include_artifacts:
            for detection in selected:
                detection["crop_jpeg_base64"] = self._encode_jpeg(
                    detection["_crop_bgr"]
                )

        summary = _condition_summary(accepted)
        response: dict[str, Any] = {
            "source_id": source_id,
            "width": width,
            "height": height,
            "status": (
                "ok" if accepted else "no_reliable_coral_detected"
            ),
            **summary,
            "raw_detection_count": len(detections),
            "accepted_detection_count": len(accepted),
            "detections": detections,
            "selected_closeups": selected,
        }

        if include_artifacts:
            annotated = image.copy()
            for detection in detections:
                x1, y1, x2, y2 = detection["bbox_xyxy"]
                color = (40, 190, 70) if detection["accepted"] else (0, 165, 255)
                label = (
                    f"{detection['health']} {detection['confidence']:.0%}"
                    if detection["accepted"]
                    else f"Rejected {detection['confidence']:.0%}"
                )
                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                cv2.putText(
                    annotated,
                    label,
                    (x1, max(18, y1 - 7)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    color,
                    2,
                    cv2.LINE_AA,
                )
            response["annotated_image_jpeg_base64"] = self._encode_jpeg(annotated)
        return response

    def analyze_images(
        self,
        images: list[tuple[str, bytes]],
        refine_masks: bool = False,
        include_artifacts: bool = True,
    ) -> dict[str, Any]:
        if not images:
            raise ValueError("At least one image is required.")

        image_results: list[dict[str, Any]] = []
        all_accepted: list[dict[str, Any]] = []
        source_images: dict[str, Any] = {}
        for source_index, (source_name, image_bytes) in enumerate(images):
            source_id = f"{source_index}:{source_name}"
            image = self._decode_image(image_bytes)
            if refine_masks:
                source_images[source_id] = image
            result = self._analyze_image_array(
                image=image,
                source_id=source_id,
                refine_masks=False,
                include_artifacts=include_artifacts,
            )
            image_results.append(result)
            all_accepted.extend(
                item for item in result["detections"] if item["accepted"]
            )

        selected = sorted(
            all_accepted,
            key=lambda item: item["quality_score"],
            reverse=True,
        )[: self.config.max_closeups]
        selected_ids = {item["detection_id"] for item in selected}
        if refine_masks:
            for source_id, source_image in source_images.items():
                source_detections = [
                    item for item in selected if item["source_id"] == source_id
                ]
                self._segment_detections(
                    source_image,
                    source_detections,
                    include_artifacts,
                )

        for image_result in image_results:
            for detection in image_result["detections"]:
                detection["selected"] = detection["detection_id"] in selected_ids

        summary = _condition_summary(all_accepted)
        public_images: list[dict[str, Any]] = []
        for image_result in image_results:
            public_result = {
                key: value
                for key, value in image_result.items()
                if key != "selected_closeups"
            }
            public_detections: list[dict[str, Any]] = []
            for item in image_result["detections"]:
                public_item = self._public_detection(item)
                public_item.pop("crop_jpeg_base64", None)
                segmentation = public_item.get("segmentation")
                if segmentation:
                    segmentation = dict(segmentation)
                    segmentation.pop("mask_png_base64", None)
                    public_item["segmentation"] = segmentation
                public_detections.append(public_item)
            public_result["detections"] = public_detections
            public_images.append(public_result)

        return {
            "status": "ok" if all_accepted else "no_reliable_coral_detected",
            **summary,
            "images_analyzed": len(images),
            "raw_detection_count": sum(
                result["raw_detection_count"] for result in image_results
            ),
            "accepted_detection_count": len(all_accepted),
            "selected_closeups": [
                self._public_detection(item) for item in selected
            ],
            "images": public_images,
            "reliability_gate": {
                "minimum_confidence": self.config.min_confidence,
                "area_ratio_range": [
                    self.config.min_area_ratio,
                    self.config.max_area_ratio,
                ],
                "minimum_laplacian_sharpness": self.config.min_sharpness,
            },
        }

    def analyze_video(
        self,
        video_bytes: bytes,
        filename: str = "upload.mp4",
        include_artifacts: bool = True,
    ) -> dict[str, Any]:
        if not video_bytes:
            raise ValueError("The uploaded video is empty.")

        cv2, _ = self._cv_runtime()
        suffix = Path(filename).suffix or ".mp4"
        temporary_path: str | None = None
        capture: Any = None
        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp:
                temp.write(video_bytes)
                temporary_path = temp.name

            capture = cv2.VideoCapture(temporary_path)
            if not capture.isOpened():
                raise ValueError("The uploaded file is not a readable video.")

            fps = float(capture.get(cv2.CAP_PROP_FPS))
            if not math.isfinite(fps) or fps <= 0:
                fps = 25.0
            frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
            sample_step = max(1, int(round(fps / self.config.video_target_fps)))

            frame_index = 0
            analyzed_frames = 0
            all_candidates: list[dict[str, Any]] = []
            while analyzed_frames < self.config.max_video_frames:
                ok, frame = capture.read()
                if not ok:
                    break
                if frame_index % sample_step == 0:
                    timestamp_seconds = frame_index / fps
                    result = self._analyze_image_array(
                        image=frame,
                        source_id=f"frame-{frame_index}",
                        refine_masks=False,
                        include_artifacts=False,
                    )
                    for detection in result["detections"]:
                        if detection["accepted"]:
                            detection["frame_index"] = frame_index
                            detection["timestamp_seconds"] = round(
                                timestamp_seconds, 3
                            )
                            all_candidates.append(detection)
                    analyzed_frames += 1
                frame_index += 1

            unique_selected: list[dict[str, Any]] = []
            for candidate in sorted(
                all_candidates,
                key=lambda item: item["quality_score"],
                reverse=True,
            ):
                is_duplicate = any(
                    self._hash_distance(
                        candidate["_crop_hash"], chosen["_crop_hash"]
                    )
                    <= self.config.duplicate_hash_distance
                    for chosen in unique_selected
                )
                if not is_duplicate:
                    unique_selected.append(candidate)
                if len(unique_selected) >= self.config.max_closeups:
                    break

            if include_artifacts:
                for detection in unique_selected:
                    detection["crop_jpeg_base64"] = self._encode_jpeg(
                        detection["_crop_bgr"]
                    )

            summary = _condition_summary(unique_selected)
            duration_seconds = frame_count / fps if frame_count > 0 else None
            return {
                "status": (
                    "ok"
                    if unique_selected
                    else "no_reliable_coral_detected"
                ),
                **summary,
                "filename": filename,
                "video": {
                    "fps": round(fps, 3),
                    "frame_count": frame_count,
                    "duration_seconds": (
                        round(duration_seconds, 3)
                        if duration_seconds is not None
                        else None
                    ),
                    "sample_step_frames": sample_step,
                    "frames_analyzed": analyzed_frames,
                },
                "accepted_candidate_count": len(all_candidates),
                "selected_closeups": [
                    self._public_detection(item) for item in unique_selected
                ],
                "duplicate_rule": {
                    "algorithm": "difference_hash_64_bit",
                    "maximum_hamming_distance": (
                        self.config.duplicate_hash_distance
                    ),
                },
                "reliability_gate": {
                    "minimum_confidence": self.config.min_confidence,
                    "area_ratio_range": [
                        self.config.min_area_ratio,
                        self.config.max_area_ratio,
                    ],
                    "minimum_laplacian_sharpness": self.config.min_sharpness,
                },
            }
        finally:
            if capture is not None:
                capture.release()
            if temporary_path and os.path.exists(temporary_path):
                os.unlink(temporary_path)


VISION_SERVICE = CoralVisionService()
