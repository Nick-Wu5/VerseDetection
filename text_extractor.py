#!/usr/bin/env python3
"""
Text extraction module for verse detection.
Handles OCR text extraction and text cleaning.
"""

import cv2 as cv
import numpy as np
import re
from typing import List, Dict, Tuple
from google.cloud import vision

class TextExtractor:
    """Extracts and processes text from image regions."""
    
    def __init__(self):
        self.client = None
        self.initialize_vision_client()
    
    def initialize_vision_client(self):
        """Initialize Google Cloud Vision client."""
        try:
            self.client = vision.ImageAnnotatorClient()
            print("✅ Google Cloud Vision API client initialized")
        except Exception as e:
            print(f"❌ Error initializing Google Cloud Vision API: {e}")
            self.client = None
    
    def extract_text_from_regions(self, underlines: List, original_image: np.ndarray, 
                                search_height: int = 50, expand_context: bool = True) -> Dict[int, str]:
        """
        Extract text regions above each detected underline.
        
        Args:
            underlines: List of detected underline coordinates [(x1, y1, x2, y2), ...]
            original_image: Original BGR image for OCR processing
            search_height: Vertical distance above underline to search for text
            expand_context: If True, expand text extraction to capture full verse context
        
        Returns:
            Dictionary mapping underline index to extracted text
        """
        if self.client is None:
            print("❌ Google Cloud Vision API client not initialized")
            return {}
        
        text_regions = {}
        
        # Get image dimensions
        height, width = original_image.shape[:2]
        
        # Sort underlines by y-coordinate to process from top to bottom
        sorted_underlines = sorted(enumerate(underlines), key=lambda x: x[1][0][1])
        
        for i, (original_idx, line) in enumerate(sorted_underlines):
            x1, y1, x2, y2 = line[0]
            y_underline = int(y1)
            
            # Skip underlines that are too close to the top margin (likely noise)
            margin_threshold = 100  # pixels from top
            if y_underline < margin_threshold:
                print(f"Underline {original_idx}: Skipping - too close to top margin (y={y_underline})")
                text_regions[original_idx] = ""
                continue
            
            # Calculate expanded search region for better verse context
            if expand_context:
                # Expand horizontally to capture full verse width
                x_expand = int(width * 0.1)  # 10% of image width on each side
                x_start = max(0, x1 - x_expand)
                x_end = min(width, x2 + x_expand)
                
                # Expand vertically to capture more context above and below
                y_expand = int(search_height * 0.3)  # 30% more vertical context
                y_start = max(0, y_underline - search_height - y_expand)
                y_end = min(height, y_underline + y_expand)  # Also look below underline
            else:
                # Original behavior
                x_start, x_end = x1, x2
                y_start = max(0, y_underline - search_height)
                y_end = y_underline
            
            # Extract expanded text region
            text_region = original_image[y_start:y_end, x_start:x_end]
            
            try:
                # Convert BGR to RGB (Google Cloud Vision expects RGB)
                text_region_rgb = cv.cvtColor(text_region, cv.COLOR_BGR2RGB)
                
                # Convert to bytes for Google Cloud Vision API
                success, buffer = cv.imencode('.png', text_region_rgb)
                if not success:
                    print(f"Error encoding image for underline {original_idx}")
                    text_regions[original_idx] = ""
                    continue
                
                image_bytes = buffer.tobytes()
                
                # Create image object for Google Cloud Vision
                image = vision.Image(content=image_bytes)
                
                # Perform text detection
                response = self.client.text_detection(image=image)
                
                # Check for API errors
                if hasattr(response, 'error') and response.error.message:
                    print(f"Underline {original_idx}: Google Cloud Vision API error: {response.error.message}")
                    text_regions[original_idx] = ""
                    continue
                
                texts = response.text_annotations
                
                if texts:
                    # Get the first (and usually only) text annotation
                    extracted_text = texts[0].description.strip()
                    if extracted_text:
                        # Clean up the extracted text
                        cleaned_text = self.clean_extracted_text(extracted_text)
                        text_regions[original_idx] = cleaned_text
                        print(f"Underline {original_idx}: Found text '{cleaned_text}' at y={y_underline}")
                    else:
                        print(f"Underline {original_idx}: No text found above underline at y={y_underline}")
                        text_regions[original_idx] = ""
                else:
                    print(f"Underline {original_idx}: No text detected above underline at y={y_underline}")
                    text_regions[original_idx] = ""
                    
            except Exception as e:
                print(f"Error extracting text for underline {original_idx}: {e}")
                text_regions[original_idx] = ""
        
        return text_regions
    
    def clean_extracted_text(self, text: str) -> str:
        """
        Clean and format extracted text to improve readability.
        
        Args:
            text: Raw text from Google Cloud Vision API
            
        Returns:
            Cleaned and formatted text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Remove common OCR artifacts
        text = text.replace('|', 'I')  # Common OCR mistake
        text = text.replace('0', 'O')  # Common OCR mistake in certain fonts
        
        # Remove page numbers and headers that might be captured
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip lines that are likely page numbers or headers
            if (len(line) < 3 or  # Too short
                line.isdigit() or  # Just numbers
                line.startswith('Page') or  # Page headers
                line.startswith('Chapter') or  # Chapter headers
                re.match(r'^[A-Z\s]+$', line)):  # ALL CAPS headers
                continue
            cleaned_lines.append(line)
        
        return ' '.join(cleaned_lines)
    
    def extract_text_from_single_region(self, image_region: np.ndarray) -> str:
        """
        Extract text from a single image region.
        
        Args:
            image_region: BGR image region to extract text from
            
        Returns:
            Extracted text string
        """
        if self.client is None:
            return ""
        
        try:
            # Convert BGR to RGB
            image_region_rgb = cv.cvtColor(image_region, cv.COLOR_BGR2RGB)
            
            # Convert to bytes
            success, buffer = cv.imencode('.png', image_region_rgb)
            if not success:
                return ""
            
            image_bytes = buffer.tobytes()
            image = vision.Image(content=image_bytes)
            
            # Perform text detection
            response = self.client.text_detection(image=image)
            
            if hasattr(response, 'error') and response.error.message:
                return ""
            
            texts = response.text_annotations
            if texts:
                return texts[0].description.strip()
            
            return ""
            
        except Exception as e:
            print(f"Error extracting text from region: {e}")
            return ""
