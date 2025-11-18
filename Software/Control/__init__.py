"""
Control Layer
-------------

The Control layer contains high-level orchestrators implementing
application logic such as:

    - computer vision pipelines (ALPR, tracking…)
    - decision logic
    - multi-service coordination
    - data fusion

This layer MUST NOT depend on:
    - hardware interfaces (Drivers, Interface)
    - driver-level types (Frame, etc.)

It only consumes:
    - Service layer abstractions (CameraService, …)
    - Domain types (ImageFrame)
    - ML_Models (YOLO, OCR)
    - Algorithms (ROI extraction, preprocessing)

Controllers expose a clean API to the App layer.
"""

from .lpd_control import LPDControl

__all__ = [
    "LPDControl",
]
