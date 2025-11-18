# Software/Control/lpd_control.py
"""
LPDControl (License Plate Detection Controller)
-----------------------------------------------

High-level ALPR detection orchestrator running in a background thread.

Responsibilities:
    - Pull ImageFrame objects from CameraService (non-blocking)
    - Invoke YOLO detector via YoloDetectorService (Service Layer)
    - (Future) Call ROIExtractionService for cropping
    - (Future) Call PlatePreprocessService for image cleaning
    - (Future) Call OCRService for plate text recognition
    - Store results + processed debug frames thread-safe
    - Provide a clean API for App & Debug Display

This controller MUST NOT:
    - depend on driver-level Frame objects (Interface layer)
    - contain ML logic
    - contain hardware logic
    - perform heavy OpenCV processing

It orchestrates the ALPR pipeline:
    Service → Control → (future services) → App
"""

from __future__ import annotations
import threading
import time
from typing import Optional, Any

import cv2  # Only for lightweight debug overlays

from Software.Service.camera_service import CameraService, ImageFrame
from Software.Service.yolo_detector_service import YoloDetectorService
# from Software.Service.roi_extraction_service import ROIExtractionService
# from Software.Service.preprocess_service import PlatePreprocessService
# from Software.Service.ocr_service import OCRService


class LPDControl:
    """
    High-level License Plate Detection controller.

    The controller:
        - retrieves ImageFrame objects from CameraService
        - delegates detection to YoloDetectorService
        - will delegate ROI extraction / preprocessing / OCR to dedicated services
        - prepares a processed debug frame (optional)
        - outputs structured detection results

    It does NOT:
        - know about camera drivers
        - know about Interface.Frame
        - implement any ML logic directly
    """

    # ------------------------------------------------------------------
    # Constructor
    # ------------------------------------------------------------------
    def __init__(self, camera_service: CameraService) -> None:
        self._camera_service = camera_service

        # Thread state
        self._running: bool = False
        self._thread: threading.Thread | None = None

        # Shared outputs (thread-safe)
        self._latest_result: Optional[Any] = None
        self._latest_frame_processed: Optional[Any] = None
        self._lock = threading.Lock()

        # Load YOLO model through a Service (not directly)
        self._detector = YoloDetectorService(
            "Software/Service/ML_Models/license_plate_detector.pt"
        )

        # Future ALPR services:
        # self._roi_service = ROIExtractionService()
        # self._preprocess_service = PlatePreprocessService()
        # self._ocr_service = OCRService()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def start(self) -> None:
        """Start background detection thread."""
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
    # Background loop
    # ------------------------------------------------------------------
    def _loop(self) -> None:
        """Main inference loop."""
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
    # Detection Pipeline
    # ------------------------------------------------------------------
    def _run_pipeline(self, frame: ImageFrame) -> tuple[Any | None, Any]:
        """
        ALPR pipeline:
            Step 1 — YOLO detection (YoloDetectorService)
            Step 2 — (Future) ROI extraction (ROIExtractionService)
            Step 3 — (Future) Preprocessing (PlatePreprocessService)
            Step 4 — (Future) OCR recognition (OCRService)
            Step 5 — lightweight debug overlay

        Returns:
            result_dict or None, processed_frame (numpy BGR)
        """

        img = frame.data
        processed = img.copy()

        # --- Step 1: YOLO detection ---
        detections = self._detector.detect(img)
        if not detections:
            return None, processed

        x, y, w, h, conf = detections[0]  # highest confidence

        # --- Step 2: Future ALPR services ---
        # roi = self._roi_service.extract(img, (x, y, w, h))
        # plate_clean = self._preprocess_service.process(roi)
        # text = self._ocr_service.read(plate_clean)

        # --- Step 3: Structured result ---
        result = {
            "bbox": (x, y, w, h),
            "confidence": conf,
            "timestamp": frame.timestamp,
            # "plate_text": text,
        }

        # --- Step 4: Debug overlay ---
        cv2.rectangle(processed, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(
            processed,
            f"{conf:.2f}",
            (x, y - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
        )

        return result, processed

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_latest_result(self) -> Optional[Any]:
        """Return the latest structured ALPR result."""
        with self._lock:
            return self._latest_result

    def get_latest_frame(self) -> Optional[Any]:
        """Return the latest processed debug frame."""
        with self._lock:
            return self._latest_frame_processed
