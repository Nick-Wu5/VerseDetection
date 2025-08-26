#!/usr/bin/env python3
"""
Main verse detection pipeline.
Orchestrates all modules to detect and extract Bible verses from underlined text.
"""

import cv2 as cv
import numpy as np
from typing import Dict, List, Tuple
import os
import sys

from image_preprocessor import ImagePreprocessor
from underline_detector_module import UnderlineDetector
from text_extractor import TextExtractor
from verse_processor import VerseProcessor, VerseBlock
from debug_visualizer import DebugVisualizer

class VerseDetectionPipeline:
    """Main pipeline for verse detection from underlined Bible text."""
    
    def __init__(self, show_visual_steps: bool = False, enable_debug_visualizer: bool = False):
        self.show_visual_steps = show_visual_steps
        self.enable_debug_visualizer = enable_debug_visualizer
        
        # Initialize modules
        self.image_preprocessor = ImagePreprocessor()
        self.underline_detector = UnderlineDetector()
        self.text_extractor = TextExtractor()
        self.verse_processor = VerseProcessor()
        
        # Initialize debug visualizer if enabled
        self.debug_visualizer = DebugVisualizer() if enable_debug_visualizer else None
        
        # Results storage
        self.detected_underlines = []
        self.extracted_text = {}
        self.detected_verses = []
        self.analysis_results = {}
    
    def process_image(self, image_path: str) -> Dict:
        """
        Process an image through the complete verse detection pipeline.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing all results and analysis
        """
        print("🚀 Starting Verse Detection Pipeline")
        print("=" * 50)
        
        try:
            # Step 1: Load and preprocess image
            if not self._load_and_preprocess_image(image_path):
                return self._create_error_result("Failed to load or preprocess image")
            
            # Step 2: Detect underlines
            if not self._detect_underlines():
                return self._create_error_result("Failed to detect underlines")
            
            # Step 3: Extract text from underline regions
            if not self._extract_text_from_underlines():
                return self._create_error_result("Failed to extract text from underlines")
            
            # Step 4: Process and analyze verses
            if not self._process_verses():
                return self._create_error_result("Failed to process verses")
            
            # Step 5: Analyze results
            self._analyze_results()
            
            # Step 6: Display results
            self._display_results()
            
            return self._create_success_result()
            
        except Exception as e:
            print(f"❌ Pipeline error: {e}")
            return self._create_error_result(f"Pipeline error: {e}")
    
    def _load_and_preprocess_image(self, image_path: str) -> bool:
        """Step 1: Load and preprocess the image."""
        print("\n📸 Step 1: Loading and preprocessing image...")
        
        # Load image
        if not self.image_preprocessor.load_image(image_path):
            return False
        
        # Preprocess image
        gray_image = self.image_preprocessor.preprocess_image(show_steps=self.show_visual_steps)
        
        # Create text mask
        text_mask = self.image_preprocessor.create_text_mask(gray_image, show_steps=self.show_visual_steps)
        
        if text_mask is None:
            return False
        
        # Add debug visualization if enabled
        if self.debug_visualizer:
            self.debug_visualizer.add_debug_stage(
                "Text Mask", 
                text_mask, 
                "Binary text mask after preprocessing and cleaning"
            )
        
        print("✅ Image preprocessing completed")
        return True
    
    def _detect_underlines(self) -> bool:
        """Step 2: Detect underlines in the text mask."""
        print("\n🔍 Step 2: Detecting underlines...")
        
        text_mask = self.image_preprocessor.get_text_mask()
        height, width = self.image_preprocessor.get_image_dimensions()
        
        # Detect underlines
        detected_lines = self.underline_detector.detect_underlines(
            text_mask, width, show_steps=self.show_visual_steps
        )
        
        if not detected_lines:
            print("⚠️ No underlines detected")
            return False
        
        # Filter horizontal lines with text presence validation
        horizontal_lines = self.underline_detector.filter_horizontal_lines(
            detected_lines, width, height, text_mask
        )
        
        if not horizontal_lines:
            print("⚠️ No valid horizontal underlines found after filtering")
            return False
        
        # Merge nearby segments
        merged_lines = self.underline_detector.merge_nearby_segments(horizontal_lines)
        
        self.detected_underlines = merged_lines
        
        # Add debug visualization if enabled
        if self.debug_visualizer:
            # Get original image for visualization
            original_image = self.image_preprocessor.get_original_image()
            
            # Visualize detected underlines
            underline_vis = self.debug_visualizer.visualize_underlines(
                original_image, merged_lines, show_numbers=True
            )
            
            self.debug_visualizer.add_debug_stage(
                "Detected Underlines", 
                underline_vis, 
                f"Detected {len(merged_lines)} underlines with numbering"
            )
        
        print(f"✅ Underline detection completed: {len(merged_lines)} underlines found")
        return True
    
    def _extract_text_from_underlines(self) -> bool:
        """Step 3: Extract text from regions above underlines."""
        print("\n📝 Step 3: Extracting text from underline regions...")
        
        original_image = self.image_preprocessor.get_original_image()
        
        # Extract text from each underline region
        self.extracted_text = self.text_extractor.extract_text_from_regions(
            self.detected_underlines, 
            original_image, 
            expand_context=True
        )
        
        # Count non-empty text regions
        non_empty_count = sum(1 for text in self.extracted_text.values() if text.strip())
        
        if non_empty_count == 0:
            print("⚠️ No text extracted from any underline regions")
            return False
        
        # Add debug visualization if enabled
        if self.debug_visualizer:
            original_image = self.image_preprocessor.get_original_image()
            
            # Visualize text extraction regions
            text_region_vis = self.debug_visualizer.visualize_text_regions(
                original_image, self.detected_underlines, self.extracted_text
            )
            
            self.debug_visualizer.add_debug_stage(
                "Text Extraction Regions", 
                text_region_vis, 
                f"Text extraction regions: {non_empty_count} with content, {len(self.extracted_text) - non_empty_count} empty"
            )
        
        print(f"✅ Text extraction completed: {non_empty_count} regions with text")
        return True
    
    def _process_verses(self) -> bool:
        """Step 4: Process extracted text to identify and group verses."""
        print("\n📖 Step 4: Processing and grouping verses...")
        
        # Get underline positions for verse processing
        underline_positions = []
        for line in self.detected_underlines:
            x1, y1, x2, y2 = line[0]
            underline_positions.append((int(x1), int(y1), int(x2), int(y2)))
        
        # Detect verse blocks
        verse_blocks = self.verse_processor.detect_verse_blocks(
            self.extracted_text, underline_positions
        )
        
        if not verse_blocks:
            print("⚠️ No verses detected in extracted text")
            return False
        
        # Group related verses
        grouped_verses = self.verse_processor.group_related_verses(verse_blocks)
        
        self.detected_verses = grouped_verses
        
        # Add debug visualization if enabled
        if self.debug_visualizer and grouped_verses:
            original_image = self.image_preprocessor.get_original_image()
            
            # Visualize verse blocks
            verse_vis = self.debug_visualizer.visualize_verse_blocks(
                original_image, grouped_verses, self.detected_underlines
            )
            
            self.debug_visualizer.add_debug_stage(
                "Verse Blocks", 
                verse_vis, 
                f"Detected {len(grouped_verses)} verse groups with color coding"
            )
        
        print(f"✅ Verse processing completed: {len(grouped_verses)} verse groups detected")
        return True
    
    def _analyze_results(self):
        """Step 5: Analyze the quality and completeness of results."""
        print("\n📊 Step 5: Analyzing results...")
        
        # Analyze verse quality
        self.analysis_results = self.verse_processor.analyze_verse_quality(self.detected_verses)
        
        print("✅ Analysis completed")
    
    def _display_results(self):
        """Step 6: Display final results."""
        print("\n🎯 Final Results")
        print("=" * 50)
        
        # Display underline detection results
        print(f"📏 Underlines detected: {len(self.detected_underlines)}")
        
        # Display text extraction results
        non_empty_text = sum(1 for text in self.extracted_text.values() if text.strip())
        print(f"📝 Text regions with content: {non_empty_text}")
        
        # Display verse detection results
        print(f"📖 Verses detected: {len(self.detected_verses)}")
        
        # Display quality analysis
        if self.analysis_results:
            print(f"📊 Average confidence: {self.analysis_results['average_confidence']:.2f}")
            print(f"📊 Completeness score: {self.analysis_results['completeness_score']:.2f}")
            
            if self.analysis_results['quality_issues']:
                print("\n⚠️ Quality issues detected:")
                for issue in self.analysis_results['quality_issues']:
                    print(f"   • {issue}")
        
        # Display detected verses
        if self.detected_verses:
            print(f"\n📖 Detected Verses:")
            for i, verse in enumerate(self.detected_verses):
                print(f"   {i+1}. {verse.verse_number}: {verse.content[:60]}...")
    
    def _create_success_result(self) -> Dict:
        """Create a success result dictionary."""
        return {
            'success': True,
            'underlines_detected': len(self.detected_underlines),
            'text_regions_extracted': len(self.extracted_text),
            'verses_detected': len(self.detected_verses),
            'analysis': self.analysis_results,
            'verses': self.detected_verses,
            'extracted_text': self.extracted_text
        }
    
    def _create_error_result(self, error_message: str) -> Dict:
        """Create an error result dictionary."""
        return {
            'success': False,
            'error': error_message,
            'underlines_detected': 0,
            'text_regions_extracted': 0,
            'verses_detected': 0
        }
    
    def get_visualization_image(self) -> np.ndarray:
        """Get image with detected underlines drawn on it."""
        if not self.detected_underlines:
            return None
        
        original_image = self.image_preprocessor.get_original_image()
        return self.underline_detector.draw_detected_underlines(original_image, self.detected_underlines)
    
    def show_debug_visualization(self, wait_for_key: bool = True):
        """Show comprehensive debug visualization if debug visualizer is enabled."""
        if not self.debug_visualizer:
            print("❌ Debug visualizer not enabled. Create pipeline with enable_debug_visualizer=True")
            return
        
        self.debug_visualizer.show_debug_windows(wait_for_key)
    
    def save_debug_images(self, output_dir: str = "debug_output"):
        """Save all debug images to a directory."""
        if not self.debug_visualizer:
            print("❌ Debug visualizer not enabled. Create pipeline with enable_debug_visualizer=True")
            return
        
        self.debug_visualizer.save_debug_images(output_dir)
    
    def get_debug_summary(self) -> str:
        """Get a text summary of all debug stages."""
        if not self.debug_visualizer:
            return "Debug visualizer not enabled"
        
        return self.debug_visualizer.create_debug_summary()
    
    def save_results(self, output_path: str):
        """Save results to a file."""
        # This could be expanded to save results in various formats
        print(f"💾 Results saved to: {output_path}")
    
    def cleanup(self):
        """Clean up resources and close windows."""
        if self.show_visual_steps:
            cv.destroyAllWindows()
        
        if self.debug_visualizer:
            self.debug_visualizer.cleanup()
