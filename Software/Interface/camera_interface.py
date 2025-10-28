# from Software.Drivers.camera_driver import CameraDriver
# Software/Interface/camera_interface.py
from __future__ import annotations

import abc
import time
from dataclasses import dataclass
from typing import Generator, Any


# ==============================
# Data Structures
# ==============================

@dataclass(frozen=True)
class Resolution:
    """Image resolution in pixels."""
    width: int
    height: int


@dataclass
class Frame:
    """
    Normalized frame data structure.

    Attributes:
        data: Raw frame buffer (bytes, memoryview, or numpy array).
              Numpy array allowed but not required (no hard dependency here).
        width: Frame width in pixels.
        height: Frame height in pixels.
        channels: Number of color channels (e.g., 1 for gray, 3 for RGB/BGR).
        pixel_format: Pixel layout, e.g., "BGR", "RGB", "GRAY8", "YUV420".
        timestamp: Capture timestamp (seconds, time.monotonic()).
    """
    data: bytes | memoryview | Any
    width: int
    height: int
    channels: int
    pixel_format: str
    timestamp: float


@dataclass
class CameraConfig:
    """
    Generic camera configuration object.

    Each backend can ignore unsupported fields, but MUST reflect
    the actually applied state in `current_config`.
    """
    resolution: Resolution = Resolution(1280, 720)
    framerate: float = 30.0
    pixel_format: str = "BGR"
    rotation_deg: int = 0      # Rotation (0, 90, 180, 270)
    hflip: bool = False
    vflip: bool = False

    # Exposure / ISO
    auto_exposure: bool = True
    exposure_time_us: int | None = None  # Ignored if auto_exposure=True
    iso: int | None = None               # If supported

    # White balance
    auto_white_balance: bool = True
    white_balance_gain_r: float | None = None
    white_balance_gain_b: float | None = None

    # Focus
    auto_focus: bool = True
    focus_distance_m: float | None = None  # Manual focus distance in meters

    # Region of interest (ROI) in normalized coordinates [0..1]
    roi_norm: tuple[float, float, float, float] | None = None


# ==============================
# Custom Exceptions
# ==============================

class CameraError(Exception):
    """Base exception for camera-related errors."""


class CameraOpenError(CameraError):
    """Raised when camera opening fails."""


class CameraStateError(CameraError):
    """Raised when a method is called in an invalid state."""


class CameraTimeout(CameraError):
    """Raised when frame reading times out."""


# ==============================
# Abstract Camera Interface
# ==============================

class CameraInterface(abc.ABC):
    """
    Abstract base class defining a generic camera interface.

    Typical lifecycle:
        cam.open(config)
        cam.start_stream()
        cam.read() ...
        cam.stop_stream()
        cam.close()

    Implementation notes:
      - Implementations MUST update `is_open` and `is_streaming` states properly.
      - `read()` MUST raise CameraTimeout on timeout.
      - `set_config()` may apply partial settings if not all are supported,
        but must always return the actual configuration applied.
      - `capture()` should return a still frame (useful for snapshots or debugging).
      - `frames()` provides a generator for continuous frame streaming.
    """

    _is_open: bool = False
    _is_streaming: bool = False
    _current_config: CameraConfig = CameraConfig()
    _name: str = "GenericCamera"

    # ------------------ Read-only properties ------------------
    @property
    def name(self) -> str:
        """Human-readable camera name (e.g., 'Picamera2', 'OpenCV:0', 'Libcamera CSI-2')."""
        return self._name

    @property
    def is_open(self) -> bool:
        """True if camera resource is opened."""
        return self._is_open

    @property
    def is_streaming(self) -> bool:
        """True if continuous video capture is active."""
        return self._is_streaming

    @property
    def current_config(self) -> CameraConfig:
        """Return the actual configuration applied to the camera."""
        return self._current_config

    # ------------------ Lifecycle management ------------------
    @abc.abstractmethod
    def open(self, config: CameraConfig | None = None) -> None:
        """Open the camera and optionally apply an initial configuration."""
        raise NotImplementedError

    @abc.abstractmethod
    def close(self) -> None:
        """Close the camera and release all resources."""
        raise NotImplementedError

    @abc.abstractmethod
    def start_stream(self) -> None:
        """Start continuous video streaming."""
        raise NotImplementedError

    @abc.abstractmethod
    def stop_stream(self) -> None:
        """Stop continuous video streaming."""
        raise NotImplementedError

    # ------------------ Frame acquisition ------------------
    @abc.abstractmethod
    def read(self, timeout: float | None = 2.0) -> Frame:
        """
        Retrieve a frame from the video stream.

        Args:
            timeout: Timeout in seconds (None = blocking).

        Raises:
            CameraTimeout: If no frame is received within timeout.
            CameraStateError: If called while not streaming.
        """
        raise NotImplementedError

    def frames(self, timeout: float | None = 2.0) -> Generator[Frame, None, None]:
        """
        Frame generator helper.

        Example:
            for frame in cam.frames():
                process(frame)

        Stops when `stop_stream()` is called.
        """
        while self.is_streaming:
            yield self.read(timeout=timeout)

    @abc.abstractmethod
    def flush(self) -> None:
        """Clear internal buffers (useful after configuration changes or long delays)."""
        raise NotImplementedError

    # ------------------ Single capture ------------------
    @abc.abstractmethod
    def capture(self, path: str | None = None) -> Frame:
        """
        Capture a single still image.

        Args:
            path: Optional file path to save the image.
        Returns:
            Captured frame.
        """
        raise NotImplementedError

    # ------------------ Configuration ------------------
    @abc.abstractmethod
    def set_config(self, config: CameraConfig) -> CameraConfig:
        """
        Apply a new configuration (best-effort).

        Returns:
            The configuration actually applied.
        """
        raise NotImplementedError

    # Convenience configuration helpers
    def set_resolution(self, width: int, height: int) -> CameraConfig:
        """Set camera resolution."""
        cfg = self.current_config
        cfg = CameraConfig(**{**cfg.__dict__, "resolution": Resolution(width, height)})
        return self.set_config(cfg)

    def set_framerate(self, fps: float) -> CameraConfig:
        """Set camera framerate."""
        cfg = self.current_config
        cfg = CameraConfig(**{**cfg.__dict__, "framerate": fps})
        return self.set_config(cfg)

    def set_exposure(self, auto: bool, exposure_time_us: int | None = None, iso: int | None = None) -> CameraConfig:
        """Enable/disable auto exposure and optionally set manual exposure time or ISO."""
        cfg = self.current_config
        cfg = CameraConfig(
            **{
                **cfg.__dict__,
                "auto_exposure": auto,
                "exposure_time_us": exposure_time_us if not auto else None,
                "iso": iso,
            }
        )
        return self.set_config(cfg)

    def set_white_balance(self, auto: bool, gain_r: float | None = None, gain_b: float | None = None) -> CameraConfig:
        """Enable/disable auto white balance and optionally set manual RGB gains."""
        cfg = self.current_config
        cfg = CameraConfig(
            **{
                **cfg.__dict__,
                "auto_white_balance": auto,
                "white_balance_gain_r": gain_r if not auto else None,
                "white_balance_gain_b": gain_b if not auto else None,
            }
        )
        return self.set_config(cfg)

    def set_focus(self, auto: bool, distance_m: float | None = None) -> CameraConfig:
        """Enable/disable auto focus and optionally set manual focus distance."""
        cfg = self.current_config
        cfg = CameraConfig(
            **{
                **cfg.__dict__,
                "auto_focus": auto,
                "focus_distance_m": distance_m if not auto else None,
            }
        )
        return self.set_config(cfg)

    def set_roi(self, x: float, y: float, w: float, h: float) -> CameraConfig:
        """
        Set normalized region of interest (ROI).

        Args:
            x, y, w, h: Normalized coordinates in [0..1].

        Note:
            Implementation may round to hardware alignment (e.g. 2x2 or 16x16 blocks).
        """
        cfg = self.current_config
        cfg = CameraConfig(**{**cfg.__dict__, "roi_norm": (x, y, w, h)})
        return self.set_config(cfg)

    # ------------------ Backend capabilities ------------------
    @abc.abstractmethod
    def capabilities(self) -> dict[str, Any]:
        """
        Query backend capabilities.

        Example:
        {
            "resolutions": [(640,480), (1280,720), (1920,1080)],
            "pixel_formats": ["BGR", "RGB", "GRAY8", "YUV420"],
            "controls": {
                "exposure": {"auto": True, "manual": True, "min_us": 50, "max_us": 200000},
                "wb": {"auto": True, "manual_gains": True},
                "focus": {"auto": False, "manual_distance": False},
            },
            "roi_supported": True
        }
        """
        raise NotImplementedError

    # ------------------ Context manager support ------------------
    def __enter__(self) -> CameraInterface:
        """Open the camera automatically when entering a `with` block."""
        if not self.is_open:
            self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """Ensure stream is stopped and camera closed on exit."""
        try:
            if self.is_streaming:
                self.stop_stream()
        finally:
            if self.is_open:
                self.close()
