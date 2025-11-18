# Software/Service/camera_service.py
"""
CameraService - High-level camera management service.

This service encapsulates:
  - driver creation through CameraFactory,
  - continuous frame acquisition in a background thread,
  - last-frame cache management (non-blocking),
  - safe lifecycle control (open/start/stop/close).

Upper layers do NOT interact with camera drivers directly.
They only use CameraService to obtain the latest frame or capture images.

This keeps the architecture clean, testable, and hardware-independent.
"""

from __future__ import annotations
import threading
import time
from typing import Optional
from dataclasses import dataclass
import numpy as np

from Software.Config import CameraFactory
from Software.Interface.camera_interface import CameraInterface, Frame


@dataclass
class ImageFrame:
    """
    Domain-level frame abstraction used by Control.

    It exposes only the necessary information for processing:
    - numpy image array
    - timestamp

    This breaks any dependency between Control and the driver-level Frame.
    """
    data: np.ndarray
    timestamp: float


class CameraService:
    """
    High-level abstraction managing continuous camera streaming.

    The service:
        - creates the camera via CameraFactory,
        - starts a dedicated acquisition thread,
        - stores only the most recent frame (last-frame cache),
        - provides non-blocking access to the latest frame,
        - handles lifecycle cleanly.

    It shields upper layers (Control, App) from driver details.
    """

    def __init__(self) -> None:
        self._camera: CameraInterface = CameraFactory.create()
        self._thread: threading.Thread | None = None
        self._running: bool = False
        self._latest_frame: Optional[Frame] = None   # driver frame
        self._lock = threading.Lock()

    # -----------------------------------------------------------
    # Lifecycle methods
    # -----------------------------------------------------------
    def start(self) -> None:
        """Start the camera and the background acquisition thread."""
        if self._running:
            return

        self._camera.open()
        self._camera.start_stream()

        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop acquisition and release resources."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

        self._camera.stop_stream()
        self._camera.close()

    def is_running(self) -> bool:
        return self._running

    # -----------------------------------------------------------
    # Acquisition loop
    # -----------------------------------------------------------
    def _capture_loop(self) -> None:
        """Continuously read frames from the camera."""
        while self._running:
            try:
                frame = self._camera.read(timeout=1.0)

                with self._lock:
                    self._latest_frame = frame   # raw interface Frame

            except Exception:
                time.sleep(0.01)

    # -----------------------------------------------------------
    # Public API
    # -----------------------------------------------------------
    def get_latest(self) -> Optional[ImageFrame]:
        """
        Return the latest frame as a domain-level ImageFrame.

        Control never sees driver-level 'Frame' objects.

        Returns:
            ImageFrame | None
        """
        with self._lock:
            frame = self._latest_frame

        if frame is None:
            return None

        return ImageFrame(
            data=frame.data,          # numpy array
            timestamp=frame.timestamp # float
        )

    def capture(self, path: str) -> ImageFrame:
        """
        Capture a still image and return it as a domain-level ImageFrame.
        """
        frame = self._camera.capture(path)

        return ImageFrame(
            data=frame.data,
            timestamp=frame.timestamp
        )
