# Software/Service/__init__.py
"""
Service Layer

The Service layer provides high-level, hardware-independent services
built on top of the Interface layer. These services encapsulate
background processing, buffering, resource management, and system logic.

Upper layers (Control, App) interact exclusively with services,
never with drivers or hardware details.

Example:
    from Software.Service import CameraService

    service = CameraService()
    service.start()
    frame = service.get_latest()
"""

from .camera_service import CameraService
from .yolo_detector_service import YoloDetectorService
from Software.Service.roi_extraction_service import ROIExtractionService
from Software.Service.plate_preprocess_service import PlatePreprocessService

__all__ = [
    "CameraService",
    "YoloDetectorService",
    "ROIExtractionService",
    "PlatePreprocessService",
]
