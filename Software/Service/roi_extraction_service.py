# Software/Service/roi_extraction_service.py
"""
ROIExtractionService
--------------------

Service responsible for extracting a Region of Interest (ROI)
from a full-frame image.

The aim is to:
    - isolate the detected license plate area,
    - clamp coordinates safely,
    - avoid crashes on invalid bounding boxes,
    - return a clean cropped numpy array.

This service must remain lightweight and independent from:
    - ML inference (handled by YoloDetectorService)
    - control logic (handled by LPDControl)
    - OCR (future OCRService)

It simply performs bounding box cropping safely.
"""

from __future__ import annotations
import numpy as np


class ROIExtractionService:
    """
    Extracts a region of interest (ROI) from an image.

    Input:
        - image: numpy BGR array
        - bbox: (x, y, w, h) in pixel coordinates

    Output:
        - cropped ROI as numpy array
        - or None if the ROI is invalid
    """

    def __init__(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def extract(self, image: np.ndarray, bbox: tuple[int, int, int, int]) -> np.ndarray | None:
        """
        Safely extract ROI from a BGR image.

        Args:
            image: full-size numpy array (BGR)
            bbox: (x, y, w, h)

        Returns:
            roi (numpy array) or None if invalid
        """
        if image is None:
            return None

        ih, iw = image.shape[:2]
        x, y, w, h = bbox

        # Clamp coordinates to image boundaries
        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(iw, x + w)
        y2 = min(ih, y + h)

        # Validate region
        if x1 >= x2 or y1 >= y2:
            return None

        roi = image[y1:y2, x1:x2]
        return roi
