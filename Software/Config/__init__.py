# Software/Config/__init__.py
"""
Configuration package for the Software system.

This package centralizes all factory classes and configuration logic.
It acts as a high-level access point for hardware and driver selection.

Upper layers (App, Control, Service) import only from this package
to obtain preconfigured interfaces such as CameraFactory.

Example:
    from Software.Config import CameraFactory

    cam = CameraFactory.create()
    cam.start_stream()
"""

# Import the factory responsible for creating camera interface instances.
from .camera_factory import CameraFactory

# Define the public symbols of this package.
# Only CameraFactory is exposed; other internal configuration files
# remain hidden from the rest of the system.
__all__ = ["CameraFactory"]
