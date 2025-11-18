# Software/Service/yolo_detector_service.py
"""
YoloDetectorService
-------------------

Service-level wrapper around YOLO models.

This service encapsulates:
    - loading YOLO model weights (from Service/ML_Models/)
    - providing thread-safe inference
    - exposing a clean `detect(image)` API for Control layer

The Control layer MUST NOT load YOLO models directly.
It must ONLY use YoloDetectorService.

This ensures:
    - Clean Architecture (Control independent from ML framework)
    - no direct usage of .pt weights in Control
    - easy replacement of YOLO by TensorRT / OpenVINO later
"""

from __future__ import annotations
import threading
from typing import List, Tuple

import numpy as np
from ultralytics import YOLO


class YoloDetectorService:
    """
    YOLO inference service.

    This class:
        - loads the YOLO model once at startup
        - ensures thread-safe inference through a lock
        - returns bounding boxes as (x, y, w, h, conf)
    """

    def __init__(self, model_path: str) -> None:
        """Load YOLO model from the given path."""
        self._model = YOLO(model_path)
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def detect(self, image: np.ndarray) -> List[Tuple[int, int, int, int, float]]:
        """
        Run YOLO inference on a BGR numpy image.

        Returns:
            list of detections:
                (x, y, w, h, confidence)
        """
        with self._lock:
            results = self._model.predict(
                source=image,
                imgsz=640,
                conf=0.25,
                verbose=False,
            )

        detections: List[Tuple[int, int, int, int, float]] = []

        for r in results:
            if r.boxes is None:
                continue

            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = float(box.conf[0])
                w = x2 - x1
                h = y2 - y1
                detections.append((int(x1), int(y1), int(w), int(h), conf))

        return detections
