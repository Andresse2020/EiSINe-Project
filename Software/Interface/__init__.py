# Software/Interface/__init__.py
"""
Interface layer for hardware-agnostic abstractions.

This package defines pure abstract interfaces used by higher layers (App, Control, Service)
and implemented by lower-level drivers (Drivers/).

Example:
    from Software.Interface import CameraInterface
"""

from .camera_interface import CameraInterface

__all__ = [
    "CameraInterface",
]
