#!/usr/bin/env python3
"""
Image preprocessing module for verse detection.
Handles image loading, noise reduction, and text mask creation.
"""

import cv2 as cv
import numpy as np
from typing import Tuple

class ImagePreprocessor:
    """Handles image preprocessing for verse detection."""
    
    def __init__(self):
        self.processed_image = None
        self.text_mask = None
        self.height = 0
        self.width = 0
    
    def load_image(self, image_path: str) -> bool:
        """
        Load and validate an image file.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            bool: True if image loaded successfully, False otherwise
        """
        try:
            self.processed_image = cv.imread(image_path)
            if self.processed_image is None:
                print(f"❌ Error: Could not load image from {image_path}")
                return False
            
            self.height, self.width = self.processed_image.shape[:2]
            print(f"✅ Loaded image: {self.width}x{self.height}")
            return True
            
        except Exception as e:
            print(f"❌ Error loading image: {e}")
            return False
    
    def preprocess_image(self, show_steps: bool = False) -> np.ndarray:
        """
        Preprocess the loaded image for text detection.
        
        Args:
            show_steps: If True, display intermediate processing steps
            
        Returns:
            np.ndarray: Preprocessed grayscale image
        """
        if self.processed_image is None:
            raise ValueError("No image loaded. Call load_image() first.")
        
        # Convert to grayscale
        gray = cv.cvtColor(self.processed_image, cv.COLOR_BGR2GRAY)
        if show_steps:
            cv.imshow("Grayscale", gray)
        
        # Apply bilateral filter to reduce noise while preserving edges
        gray = cv.bilateralFilter(gray, 9, 75, 75)
        if show_steps:
            cv.imshow("After Bilateral Filter", gray)
        
        return gray
    
    def create_text_mask(self, gray_image: np.ndarray, show_steps: bool = False) -> np.ndarray:
        """
        Create a binary mask highlighting text regions.
        
        Args:
            gray_image: Preprocessed grayscale image
            show_steps: If True, display intermediate processing steps
            
        Returns:
            np.ndarray: Binary text mask
        """
        # Create text mask using adaptive thresholding
        text_mask = cv.adaptiveThreshold(
            gray_image, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv.THRESH_BINARY_INV, 11, 2
        )
        if show_steps:
            cv.imshow("Text Mask", text_mask)
        
        # Clean up text mask using morphological operations
        kernel = cv.getStructuringElement(cv.MORPH_RECT, (3, 3))
        text_mask = cv.morphologyEx(text_mask, cv.MORPH_CLOSE, kernel)
        text_mask = cv.morphologyEx(text_mask, cv.MORPH_OPEN, kernel)
        if show_steps:
            cv.imshow("Cleaned Text Mask", text_mask)
        
        self.text_mask = text_mask
        return text_mask
    
    def get_image_dimensions(self) -> Tuple[int, int]:
        """Get the dimensions of the loaded image."""
        return self.height, self.width
    
    def get_original_image(self) -> np.ndarray:
        """Get the original loaded image."""
        return self.processed_image.copy()
    
    def get_text_mask(self) -> np.ndarray:
        """Get the created text mask."""
        return self.text_mask.copy() if self.text_mask is not None else None
