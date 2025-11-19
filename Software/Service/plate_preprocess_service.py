# Software/Service/plate_preprocess_service.py
"""
PlatePreprocessService
----------------------

Service responsible for cleaning and normalizing a cropped license plate ROI
before feeding it to an OCR engine.

Typical operations:
    - convert to grayscale
    - resize to a standard OCR-friendly shape (e.g., 160x40)
    - histogram equalization (contrast boost)
    - Gaussian blur (noise removal)
    - optional thresholding (for classical OCR models)

This service contains NO OCR logic and NO ML.
It is purely lightweight image processing.
"""

from __future__ import annotations
import cv2
import numpy as np


class PlatePreprocessService:
    """
    Normalize license plate ROI for OCR.

    Input:
        - roi: numpy array (cropped BGR image)

    Output:
        - preprocessed image ready for OCR
        - returns None if ROI is invalid
    """

    def __init__(self, target_width: int = 160, target_height: int = 40) -> None:
        """
        Args:
            target_width: resized width for OCR models
            target_height: resized height for OCR models
        """
        self._tw = target_width
        self._th = target_height

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def process(self, roi: np.ndarray | None) -> np.ndarray | None:
        """
        Preprocess the ROI for OCR.

        Steps:
            1) validate ROI
            2) grayscale
            3) resize
            4) equalize histogram
            5) Gaussian blur
            6) (optional) thresholding

        Returns:
            cleaned_plate: numpy float32 or uint8
            None if ROI is invalid
        """
        if roi is None:
            return None

        # Check minimum size
        h, w = roi.shape[:2]
        if h < 10 or w < 30:
            return None

        # --- Step 1: grayscale ---
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        # --- Step 2: resize to OCR-friendly resolution ---
        gray = cv2.resize(gray, (self._tw, self._th), interpolation=cv2.INTER_AREA)

        # --- Step 3: histogram equalization ---
        gray = cv2.equalizeHist(gray)

        # --- Step 4: remove noise ---
        gray = cv2.GaussianBlur(gray, (3, 3), sigmaX=0)

        # --- Step 5: optional threshold ---
        # Adaptive threshold improves clarity for OCR
        # Enable if your OCR service prefers binary images
        # gray = cv2.adaptiveThreshold(
        #     gray, 255,
        #     cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        #     cv2.THRESH_BINARY,
        #     blockSize=11,
        #     C=2
        # )

        return gray
