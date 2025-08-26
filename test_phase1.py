#!/usr/bin/env python3
"""
Test script for Phase 1: Underline-to-Text Association
Tests the get_text_above_underlines function with a sample image.
"""

import cv2 as cv
import numpy as np
from underline_detector import get_text_above_underlines, merge_nearby_segments

def test_phase1():
    """Test Phase 1 functionality with a sample image."""
    
    # Test image path
    IMAGE_PATH = "Photos/proverbs_27(4-23).jpeg"
    
    try:
        # Load image
        img = cv.imread(IMAGE_PATH)
        if img is None:
            print(f"Error: Could not load image from {IMAGE_PATH}")
            return False
            
        height, width = img.shape[:2]
        print(f"Loaded image: {width}x{height}")
        
        # Process image to get text mask and underlines
        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        gray = cv.bilateralFilter(gray, 9, 75, 75)
        
        # Create text mask
        text_mask = cv.adaptiveThreshold(gray, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                        cv.THRESH_BINARY_INV, 11, 2)
        
        # Clean up text mask
        kernel = cv.getStructuringElement(cv.MORPH_RECT, (3, 3))
        text_mask = cv.morphologyEx(text_mask, cv.MORPH_CLOSE, kernel)
        text_mask = cv.morphologyEx(text_mask, cv.MORPH_OPEN, kernel)
        
        # Extract underlines
        underline_mask = np.zeros_like(text_mask)
        k_heights = [1, 2, 3]
        k_widths = [max(10, width//80), max(20, width//60), max(30, width//40)]
        
        for ky in k_heights:
            for kx in k_widths:
                kernel = cv.getStructuringElement(cv.MORPH_RECT, (kx, ky))
                eroded = cv.erode(text_mask, kernel)
                underline_mask = np.maximum(underline_mask, eroded)
        
        # Clean up underline mask
        kernel_clean = cv.getStructuringElement(cv.MORPH_RECT, (max(20, width//50), 1))
        underline_clean = cv.morphologyEx(underline_mask, cv.MORPH_CLOSE, kernel_clean)
        
        # Detect lines
        underline_binary_uint8 = np.uint8(underline_clean)
        lines = cv.HoughLinesP(underline_binary_uint8, 
                               rho=1,
                               theta=np.pi/180,
                               threshold=70,
                               minLineLength=max(50, width//20),
                               maxLineGap=35)
        
        if lines is None:
            print("No underlines detected")
            return False
        
        # Filter horizontal lines
        horizontal_lines = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if x2 - x1 != 0:
                angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
                if abs(angle) < 10 or abs(angle - 180) < 10:
                    line_length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                    if line_length > width * 0.05:
                        horizontal_lines.append(line)
        
        # Merge nearby segments
        if len(horizontal_lines) > 1:
            horizontal_lines = merge_nearby_segments(horizontal_lines, y_threshold=15, x_gap=50)
        
        print(f"Detected {len(horizontal_lines)} underlines")
        
        # Test Phase 1: Extract text above underlines
        print("\n=== Testing Phase 1: Underline-to-Text Association ===")
        text_regions = get_text_above_underlines(horizontal_lines, img)
        
        if text_regions:
            print(f"\nSuccessfully extracted text from {len(text_regions)} underlines:")
            for underline_idx, text in text_regions.items():
                print(f"  Underline {underline_idx}: '{text}'")
            return True
        else:
            print("No text extracted from underlines")
            return False
            
    except Exception as e:
        print(f"Error during testing: {e}")
        return False

if __name__ == "__main__":
    print("Testing Phase 1: Underline-to-Text Association")
    print("=" * 50)
    
    success = test_phase1()
    
    if success:
        print("\n✅ Phase 1 test completed successfully!")
    else:
        print("\n❌ Phase 1 test failed!")
    
    print("\nNote: Make sure Google Cloud Vision API is configured with proper credentials.")
    print("Set GOOGLE_APPLICATION_CREDENTIALS environment variable to your service account key file.")
