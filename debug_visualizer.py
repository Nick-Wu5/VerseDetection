#!/usr/bin/env python3
"""
Debug visualizer module for verse detection.
Provides comprehensive visual debugging capabilities.
"""

import cv2 as cv
import numpy as np
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass

@dataclass
class DebugInfo:
    """Container for debug information."""
    stage_name: str
    image: np.ndarray
    description: str
    key_points: Optional[List[Tuple[int, int]]] = None
    bounding_boxes: Optional[List[Tuple[int, int, int, int]]] = None

class DebugVisualizer:
    """Provides comprehensive visual debugging for the verse detection pipeline."""
    
    def __init__(self, window_name: str = "Verse Detection Debug"):
        self.window_name = window_name
        self.debug_stages = []
        self.current_stage = 0
        self.show_all_windows = False
        
    def add_debug_stage(self, stage_name: str, image: np.ndarray, 
                        description: str = "", key_points: List[Tuple[int, int]] = None,
                        bounding_boxes: List[Tuple[int, int, int, int]] = None):
        """Add a debug stage with image and metadata."""
        debug_info = DebugInfo(
            stage_name=stage_name,
            image=image.copy(),
            description=description,
            key_points=key_points,
            bounding_boxes=bounding_boxes
        )
        self.debug_stages.append(debug_info)
    
    def visualize_underlines(self, image: np.ndarray, underlines: List, 
                           color: Tuple[int, int, int] = (0, 255, 0), 
                           thickness: int = 3, show_numbers: bool = True) -> np.ndarray:
        """
        Visualize detected underlines with optional numbering.
        
        Args:
            image: Original image to draw on
            underlines: List of underline coordinates
            color: BGR color for underlines
            thickness: Line thickness
            show_numbers: Whether to show underline indices
            
        Returns:
            Image with drawn underlines
        """
        result_img = image.copy()
        
        for i, line in enumerate(underlines):
            x1, y1, x2, y2 = line[0]
            # Ensure coordinates are integers
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            
            # Draw the underline
            cv.line(result_img, (x1, y1), (x2, y2), color, thickness)
            
            # Add underline number if requested
            if show_numbers:
                # Position text above the line
                text_pos = (x1 + 10, y1 - 10)
                cv.putText(result_img, str(i), text_pos, 
                          cv.FONT_HERSHEY_SIMPLEX, 1.2, (255, 0, 0), 3)
        
        return result_img
    
    def visualize_text_regions(self, image: np.ndarray, underlines: List, 
                             text_regions: Dict[int, str], 
                             search_height: int = 15) -> np.ndarray:
        """
        Visualize text extraction regions above underlines.
        
        Args:
            image: Original image
            underlines: List of underline coordinates
            text_regions: Dictionary mapping underline index to extracted text
            search_height: Height of text search region above underline
            
        Returns:
            Image with text regions highlighted
        """
        result_img = image.copy()
        
        for i, line in enumerate(underlines):
            x1, y1, x2, y2 = line[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            
            # Define text search region
            y_start = max(0, y1 - search_height)
            y_end = y1
            
            # Draw rectangle around text region
            if i in text_regions and text_regions[i].strip():
                # Green for regions with text
                cv.rectangle(result_img, (x1, y_start), (x2, y_end), (0, 255, 0), 2)
                
                # Add text preview
                text_preview = text_regions[i][:30] + "..." if len(text_regions[i]) > 30 else text_regions[i]
                cv.putText(result_img, text_preview, (x1, y_start - 5), 
                          cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            else:
                # Red for regions without text
                cv.rectangle(result_img, (x1, y_start), (x2, y_end), (0, 0, 255), 2)
        
        return result_img
    
    def visualize_verse_blocks(self, image: np.ndarray, verse_blocks: List, 
                             underlines: List) -> np.ndarray:
        """
        Visualize detected verse blocks and their relationships.
        
        Args:
            image: Original image
            verse_blocks: List of detected verse blocks
            underlines: List of underline coordinates
            
        Returns:
            Image with verse blocks highlighted
        """
        result_img = image.copy()
        
        # Different colors for different verse groups
        colors = [
            (255, 0, 0),    # Blue
            (0, 255, 0),    # Green
            (0, 0, 255),    # Red
            (255, 255, 0),  # Cyan
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Yellow
        ]
        
        for i, verse in enumerate(verse_blocks):
            color = colors[i % len(colors)]
            
            # Highlight underlines associated with this verse
            for underline_idx in verse.underline_indices:
                if underline_idx < len(underlines):
                    line = underlines[underline_idx]
                    x1, y1, x2, y2 = line[0]
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    
                    # Draw thick underline
                    cv.line(result_img, (x1, y1), (x2, y2), color, 5)
                    
                    # Add verse number
                    cv.putText(result_img, verse.verse_number, (x1, y1 - 10), 
                              cv.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        
        return result_img
    
    def show_debug_windows(self, wait_for_key: bool = True):
        """Show all debug windows."""
        if not self.debug_stages:
            print("No debug stages to show")
            return
        
        print(f"\n🔍 Showing {len(self.debug_stages)} debug stages:")
        for i, stage in enumerate(self.debug_stages):
            print(f"   {i+1}. {stage.stage_name}: {stage.description}")
        
        # Show all windows
        for i, stage in enumerate(self.debug_stages):
            window_name = f"{i+1}. {stage.stage_name}"
            cv.imshow(window_name, stage.image)
            
            # Add key points if available
            if stage.key_points:
                key_img = stage.image.copy()
                for point in stage.key_points:
                    cv.circle(key_img, point, 5, (0, 255, 255), -1)
                cv.imshow(f"{i+1}. {stage.stage_name} - Key Points", key_img)
            
            # Add bounding boxes if available
            if stage.bounding_boxes:
                box_img = stage.image.copy()
                for box in stage.bounding_boxes:
                    x1, y1, x2, y2 = box
                    cv.rectangle(box_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv.imshow(f"{i+1}. {stage.stage_name} - Bounding Boxes", box_img)
        
        if wait_for_key:
            print("\n⌨️  Press any key to close debug windows...")
            cv.waitKey(0)
            cv.destroyAllWindows()
    
    def save_debug_images(self, output_dir: str = "debug_output"):
        """Save all debug images to a directory."""
        import os
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"\n💾 Saving debug images to: {output_dir}")
        
        for i, stage in enumerate(self.debug_stages):
            filename = f"{i+1:02d}_{stage.stage_name.replace(' ', '_')}.png"
            filepath = os.path.join(output_dir, filename)
            
            cv.imwrite(filepath, stage.image)
            print(f"   Saved: {filename}")
    
    def create_debug_summary(self) -> str:
        """Create a text summary of all debug stages."""
        if not self.debug_stages:
            return "No debug stages available"
        
        summary = f"Debug Summary - {len(self.debug_stages)} stages\n"
        summary += "=" * 50 + "\n"
        
        for i, stage in enumerate(self.debug_stages):
            summary += f"{i+1}. {stage.stage_name}\n"
            summary += f"   Description: {stage.description}\n"
            if stage.key_points:
                summary += f"   Key Points: {len(stage.key_points)}\n"
            if stage.bounding_boxes:
                summary += f"   Bounding Boxes: {len(stage.bounding_boxes)}\n"
            summary += "\n"
        
        return summary
    
    def clear_debug_stages(self):
        """Clear all debug stages."""
        self.debug_stages.clear()
        self.current_stage = 0
    
    def cleanup(self):
        """Clean up all windows."""
        cv.destroyAllWindows()
