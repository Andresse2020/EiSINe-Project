# Software/Drivers/opencv_camera.py
"""
OpenCV-based camera driver implementing the CameraInterface.

Compatible with headless systems (no display required).
Used for USB cameras, CSI cameras via /dev/video*, or virtual test sources.

Requirements:
    pip install opencv-python
"""

from __future__ import annotations
import cv2
import time
import threading
from typing import Any

# Import the abstract interface and its data types from the Interface layer.
# These define the contract that this concrete driver must follow.
from Software.Interface.camera_interface import (
    CameraInterface,
    CameraConfig,
    Frame,
    CameraOpenError,
    CameraStateError,
    CameraTimeout,
)


class OpenCVCamera(CameraInterface):
    """
    Concrete implementation of CameraInterface using the OpenCV backend.

    This driver wraps cv2.VideoCapture and provides a consistent API
    compatible with the rest of the system (App → Control → Service layers).

    Typical usage:
        cam = OpenCVCamera(device_index=0)
        cam.open()
        cam.start_stream()
        frame = cam.read()
        cam.stop_stream()
        cam.close()
    """

    def __init__(self, device_index: int = 0, **kwargs) -> None:
        """
        OpenCV-based camera implementation.

        Args:
            device_index: camera index (/dev/videoN)
            **kwargs: ignored additional hardware configuration fields
                      (for compatibility with factory)
        """
        super().__init__()
        self._device_index = device_index
        self._capture: cv2.VideoCapture | None = None
        self._lock = threading.Lock()
        self._name = f"OpenCVCamera[{device_index}]"

    # ------------------ Lifecycle management ------------------
    def open(self, config: CameraConfig | None = None) -> None:
        """
        Open the physical camera device and optionally apply a configuration.

        Args:
            config: Optional CameraConfig object defining resolution/framerate, etc.

        Raises:
            CameraOpenError: if the camera cannot be opened.
        """
        # If already open, do nothing
        if self._is_open:
            return

        # Try to open the video device using the V4L2 backend (Linux default)
        self._capture = cv2.VideoCapture(self._device_index, cv2.CAP_V4L2)
        if not self._capture.isOpened():
            raise CameraOpenError(f"Failed to open camera index {self._device_index}")

        # Mark state as open
        self._is_open = True

        # Apply initial configuration if provided
        if config:
            self.set_config(config)
        else:
            self._current_config = CameraConfig()

    def close(self) -> None:
        """
        Release the camera resource and reset internal state.
        Called when shutting down the camera or exiting the context manager.
        """
        if self._capture is not None:
            self._capture.release()
            self._capture = None
        self._is_open = False
        self._is_streaming = False

    def start_stream(self) -> None:
        """
        Enable continuous streaming mode.
        OpenCV handles streaming internally (no separate thread required).
        """
        if not self._is_open:
            raise CameraStateError("Cannot start stream: camera not open.")
        self._is_streaming = True

    def stop_stream(self) -> None:
        """Disable streaming mode."""
        self._is_streaming = False

    # ------------------ Frame acquisition ------------------
    def read(self, timeout: float | None = 2.0) -> Frame:
        """
        Read one frame from the active video stream.

        Args:
            timeout: Maximum wait time (in seconds) before raising CameraTimeout.

        Returns:
            Frame: Captured frame object containing image data and metadata.

        Raises:
            CameraStateError: if the camera is not streaming.
            CameraTimeout: if no valid frame is captured within the timeout.
        """
        if not self._is_streaming or self._capture is None:
            raise CameraStateError("Camera is not streaming.")

        start_time = time.monotonic()

        # Continuously attempt to read until success or timeout
        while True:
            with self._lock:
                ok, frame = self._capture.read()

            if ok:
                # OpenCV returns an ndarray (H, W, C)
                h, w, c = frame.shape
                return Frame(
                    data=frame,
                    width=w,
                    height=h,
                    channels=c,
                    pixel_format="BGR",  # OpenCV default color layout
                    timestamp=time.monotonic(),
                )

            # Check for timeout
            if timeout is not None and (time.monotonic() - start_time) > timeout:
                raise CameraTimeout("Frame read timed out.")

    def flush(self) -> None:
        """
        Discard a few buffered frames.
        Useful when latency must be reduced or after a configuration change.
        """
        if not self._capture:
            return
        for _ in range(5):
            self._capture.grab()  # grab = read frame header without decoding it

    def capture(self, path: str | None = None) -> Frame:
        """
        Capture a single still image (independent of streaming).

        Args:
            path: Optional file path to save the image (e.g., /tmp/image.jpg).

        Returns:
            Frame: Captured image as Frame object.

        Raises:
            CameraStateError: if the camera is not open.
            CameraTimeout: if capture fails.
        """
        if not self._is_open or self._capture is None:
            raise CameraStateError("Camera not open.")

        ok, frame = self._capture.read()
        if not ok:
            raise CameraTimeout("Failed to capture frame.")

        h, w, c = frame.shape
        f = Frame(
            data=frame,
            width=w,
            height=h,
            channels=c,
            pixel_format="BGR",
            timestamp=time.monotonic(),
        )

        # Optionally save image to disk (for debugging or snapshots)
        if path:
            cv2.imwrite(path, frame)

        return f

    # ------------------ Configuration ------------------
    def set_config(self, config: CameraConfig) -> CameraConfig:
        """
        Apply camera configuration (best-effort).

        Args:
            config: Configuration object specifying resolution, FPS, etc.

        Returns:
            CameraConfig: The configuration that was actually applied.

        Notes:
            - Not all parameters are supported by OpenCV/V4L2 drivers.
            - Orientation, flips, or rotation must be handled in higher layers.
        """
        if not self._capture:
            raise CameraStateError("Camera not open.")

        # Apply resolution
        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, config.resolution.width)
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, config.resolution.height)

        # Apply framerate (driver may round to nearest supported value)
        self._capture.set(cv2.CAP_PROP_FPS, config.framerate)

        # Orientation/flip will be handled by the Service layer if needed

        # Store the current configuration as applied
        self._current_config = config
        return self._current_config

    def capabilities(self) -> dict[str, Any]:
        """
        Return a minimal set of backend capabilities.
        Provides static information since OpenCV's API doesn't expose everything.

        Returns:
            dict[str, Any]: Capability dictionary containing supported modes.
        """
        if not self._capture:
            raise CameraStateError("Camera not open.")

        return {
            "resolutions": [
                (640, 480),
                (1280, 720),
                (1920, 1080),
            ],
            "pixel_formats": ["BGR"],
            "controls": {
                "exposure": {"auto": True, "manual": False},
                "wb": {"auto": True, "manual_gains": False},
                "focus": {"auto": False, "manual_distance": False},
            },
            "roi_supported": False,
        }
