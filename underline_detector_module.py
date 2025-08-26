#!/usr/bin/env python3
"""
Underline detection module for verse detection.
Handles underline detection, filtering, and merging.
"""

import cv2 as cv
import numpy as np
from typing import List, Tuple

class UnderlineDetector:
    """Detects and processes underlines in text images."""
    
    def __init__(self):
        self.detected_lines = []
        self.filtered_lines = []
        self.merged_lines = []
    
    def has_text_above_line(self, line: List, text_mask: np.ndarray, search_height: int = 15) -> bool:
        """
        Check if there's actual text content above a detected line.
        
        Args:
            line: Line coordinates [x1, y1, x2, y2]
            text_mask: Binary text mask from preprocessing
            search_height: Height of region above line to check
            
        Returns:
            bool: True if text is found above the line
        """
        x1, y1, x2, y2 = line[0]
        
        # Ensure coordinates are within bounds
        x1, x2 = max(0, min(x1, x2)), max(0, max(x1, x2))
        y_start = max(0, y1 - search_height)
        
        # Extract region above the line
        region_above = text_mask[y_start:y1, x1:x2]
        
        # Check if region has any text pixels (non-zero)
        has_text = np.any(region_above > 0)
        
        # Calculate text density for better filtering
        if has_text:
            text_density = np.sum(region_above > 0) / region_above.size
            # Require at least 2% text density to avoid very sparse text
            has_text = text_density > 0.02
        
        return has_text
    
    def detect_underlines(self, text_mask: np.ndarray, image_width: int, show_steps: bool = False) -> List:
        """
        Detect underlines from text mask using morphological operations.
        
        Args:
            text_mask: Binary text mask
            image_width: Width of the image
            show_steps: If True, display intermediate processing steps
            
        Returns:
            List: List of detected underline coordinates
        """
        # Extract underlines directly from text mask using horizontal kernels
        underline_mask = np.zeros_like(text_mask)
        k_heights = [1, 2, 3]  # Different underline thicknesses
        k_widths = [max(10, image_width//80), max(20, image_width//60), max(30, image_width//40)]
        
        for ky in k_heights:
            for kx in k_widths:
                kernel = cv.getStructuringElement(cv.MORPH_RECT, (kx, ky))
                eroded = cv.erode(text_mask, kernel)
                underline_mask = np.maximum(underline_mask, eroded)
        
        if show_steps:
            cv.imshow("Underline Mask", underline_mask)
        
        # Clean up underline mask to remove noise
        kernel_clean = cv.getStructuringElement(cv.MORPH_RECT, (max(20, image_width//50), 1))
        underline_clean = cv.morphologyEx(underline_mask, cv.MORPH_CLOSE, kernel_clean)
        if show_steps:
            cv.imshow("Cleaned Underlines", underline_clean)
        
        # Use Probabilistic Hough Line Transform
        underline_binary_uint8 = np.uint8(underline_clean)
        
        lines = cv.HoughLinesP(
            underline_binary_uint8, 
            rho=1,
            theta=np.pi/180,
            threshold=70,
            minLineLength=max(50, image_width//20),
            maxLineGap=35
        )
        
        if lines is not None:
            self.detected_lines = lines.tolist()
            print(f"🔍 Detected {len(self.detected_lines)} potential underlines")
        else:
            self.detected_lines = []
            print("🔍 No underlines detected")
        
        return self.detected_lines
    
    def filter_horizontal_lines(self, lines: List, image_width: int, image_height: int, text_mask: np.ndarray = None) -> List:
        """
        Filter lines to keep only horizontal underlines with good quality.
        Now includes text presence check for smarter noise reduction.
        
        Args:
            lines: List of detected lines
            image_width: Width of the image
            image_height: Height of the image
            text_mask: Binary text mask for text presence validation
            
        Returns:
            List: Filtered horizontal lines
        """
        horizontal_lines = []
        filtered_by_geometry = 0
        filtered_by_text = 0
        
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if x2 - x1 != 0:  # Avoid vertical lines
                angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
                
                # Keep only very horizontal lines (±10 degrees)
                if abs(angle) < 10 or abs(angle - 180) < 10:
                    line_length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                    
                    # More sophisticated filtering:
                    min_length = image_width * 0.05  # At least 5% of image width
                    max_length = image_width * 0.95  # Not longer than image width
                    margin_threshold = 80  # pixels from top/bottom
                    
                    if (line_length >= min_length and 
                        line_length <= max_length and
                        y1 > margin_threshold and 
                        y1 < image_height - margin_threshold):
                        
                        # NEW: Check if there's actually text above this line
                        if text_mask is not None:
                            if self.has_text_above_line(line, text_mask):
                                horizontal_lines.append(line)
                            else:
                                filtered_by_text += 1
                                print(f"⚠️  Filtered out line at y={y1} - no text above (page structure)")
                        else:
                            # Fallback to old behavior if no text_mask provided
                            horizontal_lines.append(line)
                    else:
                        filtered_by_geometry += 1
                else:
                    filtered_by_geometry += 1
        
        self.filtered_lines = horizontal_lines
        
        # Enhanced reporting
        total_filtered = filtered_by_geometry + filtered_by_text
        print(f"✅ Filtered to {len(horizontal_lines)} valid horizontal underlines")
        if filtered_by_geometry > 0:
            print(f"   • {filtered_by_geometry} lines filtered by geometry (length/position)")
        if filtered_by_text > 0:
            print(f"   • {filtered_by_text} lines filtered by text absence (page structure)")
        
        return horizontal_lines
    
    def merge_nearby_segments(self, lines: List, y_threshold: int = 15, x_gap: int = 50) -> List:
        """
        Merge nearby line segments into single underline intentions.
        
        Args:
            lines: List of lines to merge
            y_threshold: Maximum vertical distance for merging
            x_gap: Maximum horizontal gap for merging
            
        Returns:
            List: Merged lines
        """
        if len(lines) <= 1:
            return lines
        
        # Sort by y-coordinate first
        lines.sort(key=lambda line: line[0][1])
        
        merged = []
        current_group = [lines[0]]
        
        for line in lines[1:]:
            x1, y1, x2, y2 = line[0]
            prev_line = current_group[-1]
            prev_x1, prev_y1, prev_x2, prev_y2 = prev_line[0]
            
            # Check if lines are close vertically AND horizontally
            y_close = abs(y1 - prev_y1) <= y_threshold
            x_overlap = (x1 <= prev_x2 + x_gap) and (prev_x1 <= x2 + x_gap)
            
            if y_close and x_overlap:
                current_group.append(line)
            else:
                # Merge current group and start new one
                merged.append(self._merge_line_group(current_group))
                current_group = [line]
        
        # Don't forget the last group
        if current_group:
            merged.append(self._merge_line_group(current_group))
        
        self.merged_lines = merged
        print(f"🔗 Merged into {len(merged)} underline groups")
        return merged
    
    def _merge_line_group(self, line_group: List) -> np.ndarray:
        """Merge a group of close line segments into a single line."""
        if len(line_group) == 1:
            return line_group[0]
        
        # Find the bounding box of all lines in the group
        all_x = []
        all_y = []
        
        for line in line_group:
            x1, y1, x2, y2 = line[0]
            all_x.extend([x1, x2])
            all_y.extend([y1, y2])
        
        # Calculate the merged line
        x_min, x_max = min(all_x), max(all_x)
        y_avg = int(sum(all_y) / len(all_y))
        
        # Return a single line spanning the full width
        return np.array([[x_min, y_avg, x_max, y_avg]])
    
    def get_detection_results(self) -> Tuple[List, List, List]:
        """Get all detection results."""
        return self.detected_lines, self.filtered_lines, self.merged_lines
    
    def draw_detected_underlines(self, image: np.ndarray, lines: List, color: Tuple[int, int, int] = (0, 255, 0), thickness: int = 3) -> np.ndarray:
        """
        Draw detected underlines on the image.
        
        Args:
            image: Image to draw on
            lines: List of lines to draw
            color: BGR color tuple
            thickness: Line thickness
            
        Returns:
            np.ndarray: Image with drawn underlines
        """
        result_img = image.copy()
        
        for line in lines:
            x1, y1, x2, y2 = line[0]
            # Ensure coordinates are integers
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            cv.line(result_img, (x1, y1), (x2, y2), color, thickness)
        
        return result_img
