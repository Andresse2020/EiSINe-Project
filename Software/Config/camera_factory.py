# Software/Config/camera_factory.py
"""
CameraFactory - central entry point for selecting and instantiating the active camera driver.

This module hides all hardware details (device index, backend type, etc.)
from upper layers (App, Control, Service). The factory reads configuration
constants and returns a ready-to-use CameraInterface object.
"""

from __future__ import annotations
import importlib
from Software.Interface import CameraInterface


# ---------------------------------------------------------------------------
# GLOBAL HARDWARE CONFIGURATION
# ---------------------------------------------------------------------------

# Select which driver backend to use.
# Possible values:
#   "Software.Drivers.opencv_camera.OpenCVCamera"
#   "Software.Drivers.mock_camera.MockCamera"
#   "Software.Drivers.picamera2_camera.Picamera2Camera"
ACTIVE_CAMERA_DRIVER = "Software.Drivers.opencv_camera.OpenCVCamera"

# Default hardware parameters (used for driver constructor)
CAMERA_HARDWARE_CONFIG = {
    "device_index": 0,       # /dev/video0 or first USB camera
    "default_resolution": (640, 480),
    "default_framerate": 30.0,
}
# ---------------------------------------------------------------------------


class CameraFactory:
    """
    Factory responsible for creating a CameraInterface implementation
    according to the configuration above.

    The rest of the system remains completely unaware of the underlying hardware.
    """

    @staticmethod
    def create() -> CameraInterface:
        """
        Create and configure the active camera driver.

        Returns:
            CameraInterface: fully constructed and ready-to-use camera instance.
        """
        # Parse module path and class name
        module_path, class_name = ACTIVE_CAMERA_DRIVER.rsplit(".", 1)

        # Dynamically import driver
        module = importlib.import_module(module_path)
        driver_class = getattr(module, class_name)

        # Instantiate driver using hardware config
        camera = driver_class(**CAMERA_HARDWARE_CONFIG)

        # Optional runtime contract validation
        if not isinstance(camera, CameraInterface):
            raise TypeError(f"{class_name} does not implement CameraInterface")

        return camera
