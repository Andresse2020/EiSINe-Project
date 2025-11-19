# Software/Control/lpd_control.py
"""
LPDControl (License Plate Detection Controller)
-----------------------------------------------

High-level ALPR (License Plate Detection only, no OCR) controller.

Responsibilities:
    - Pull ImageFrame objects from CameraService (non-blocking)
    - Run YOLO detection through YoloDetectorService
    - Run ROI extraction for plate cropping (optional)
    - Run PlatePreprocessService (optional cleaning)
    - Store detection results + processed debug frames thread-safe

This controller DOES NOT:
    - use an OCR system
    - depend on driver-level Frame objects (Interface layer)
    - contain ML logic
    - contain hardware logic
    - perform heavy processing

Pipeline:
    Service → Control → App
"""

from __future__ import annotations
import threading
import time
from typing import Optional, Any

import cv2  # Only for lightweight debug overlays

from Software.Service.camera_service import CameraService, ImageFrame
from Software.Service.yolo_detector_service import YoloDetectorService
from Software.Service.roi_extraction_service import ROIExtractionService
from Software.Service.plate_preprocess_service import PlatePreprocessService


class LPDControl:
    """
    High-level License Plate Detection controller (detection only, no OCR).
    """

    # ------------------------------------------------------------------
    # Constructor
    # ------------------------------------------------------------------
    def __init__(self, camera_service: CameraService) -> None:
        self._camera_service = camera_service

        # Thread state
        self._running: bool = False
        self._thread: threading.Thread | None = None

        # Outputs shared with App layer
        self._latest_result: Optional[Any] = None
        self._latest_frame_processed: Optional[Any] = None
        self._lock = threading.Lock()

        # YOLO detector (Service Layer)
        self._detector = YoloDetectorService(
            "Software/Service/ML_Models/license_plate_detector.pt"
        )

        # Optional services only used for cropping/cleaning
        self._roi_service = ROIExtractionService()
        self._preprocess_service = PlatePreprocessService()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def start(self) -> None:
        """Start the detection thread."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._loop,
            daemon=True,
            name="LPDControlThread"
        )
        self._thread.start()

    def stop(self) -> None:
        """Stop detection thread."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def is_running(self) -> bool:
        return self._running

    # ------------------------------------------------------------------
    # Internal loop
    # ------------------------------------------------------------------
    def _loop(self) -> None:
        """Background loop for YOLO detection."""
        while self._running:

            frame = self._camera_service.get_latest()
            if frame is None:
                time.sleep(0.01)
                continue

            result, processed = self._run_pipeline(frame)

            with self._lock:
                self._latest_result = result
                self._latest_frame_processed = processed

            time.sleep(0.001)

    # ------------------------------------------------------------------
    # Pipeline (YOLO + ROI + preprocess)
    # ------------------------------------------------------------------
    def _run_pipeline(self, frame: ImageFrame) -> tuple[Any | None, Any]:
        """
        ALPR detection-only pipeline:
            1 — YOLO detection
            2 — ROI extraction (optional)
            3 — Preprocessing (optional)
            4 — Debug overlay

        Returns:
            (result_dict or None, processed_frame)
        """

        img = frame.data
        processed = img.copy()

        # ---- STEP 1 : YOLO detection ----
        detections = self._detector.detect(img)
        if not detections:
            return None, processed

        x, y, w, h, conf = detections[0]  # take best detection

        # ---- STEP 2 : ROI extraction (optional) ----
        roi = self._roi_service.extract(img, (x, y, w, h))

        # ---- STEP 3 : Preprocessing (optional) ----
        if roi is not None and roi.size > 0:
            _ = self._preprocess_service.process(roi)

        # ---- Build result ----
        result = {
            "bbox": (x, y, w, h),
            "confidence": conf,
            "timestamp": frame.timestamp,
        }

        # ---- Debug overlay ----
        self._draw_overlay(processed, x, y, w, h, conf)

        return result, processed

    # ------------------------------------------------------------------
    # Debug drawing helper
    # ------------------------------------------------------------------
    @staticmethod
    def _draw_overlay(image, x: int, y: int, w: int, h: int, conf: float) -> None:
        """Draw YOLO bounding box + confidence."""

        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

        label = f"{conf:.2f}"
        text_y = max(20, y - 5)

        cv2.putText(
            image,
            label,
            (x, text_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_latest_result(self) -> Optional[Any]:
        with self._lock:
            return self._latest_result

    def get_latest_frame(self) -> Optional[Any]:
        with self._lock:
            return self._latest_frame_processed
