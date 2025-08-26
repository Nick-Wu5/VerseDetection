#!/usr/bin/env python3
"""
Test script for debug visualization capabilities.
Demonstrates comprehensive visual debugging for the verse detection system.
"""

import os
import cv2 as cv
import numpy as np
from verse_detection_pipeline import VerseDetectionPipeline

def test_debug_visualization():
    """Test the debug visualization capabilities."""
    
    # Check Google Cloud Vision API authentication
    if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
        print("❌ GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
        print("Please set it to your service account key file path:")
        print("export GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/key.json")
        return False
    
    # Test image path
    IMAGE_PATH = "Photos/matthew_5(16-25).jpeg"
    
    if not os.path.exists(IMAGE_PATH):
        print(f"❌ Test image not found: {IMAGE_PATH}")
        return False
    
    print("🔍 Testing Debug Visualization System")
    print("=" * 60)
    
    try:
        # Create pipeline WITH debug visualizer enabled
        print("🚀 Creating pipeline with debug visualizer...")
        pipeline = VerseDetectionPipeline(
            show_visual_steps=False,  # We'll use the debug visualizer instead
            enable_debug_visualizer=True
        )
        
        # Process the image through the complete pipeline
        print("🔄 Processing image through pipeline...")
        results = pipeline.process_image(IMAGE_PATH)
        
        if results['success']:
            print("\n✅ Pipeline completed successfully!")
            
            # Display debug summary
            print("\n📊 Debug Summary:")
            print(pipeline.get_debug_summary())
            
            # Show comprehensive debug visualization
            print("\n🖼️  Showing debug visualization windows...")
            print("This will display multiple windows showing each processing stage:")
            print("  1. Text Mask - Binary mask after preprocessing")
            print("  2. Detected Underlines - Underlines with numbering")
            print("  3. Text Extraction Regions - Highlighted text regions")
            print("  4. Verse Blocks - Color-coded verse groups")
            
            # Show all debug windows
            pipeline.show_debug_visualization(wait_for_key=True)
            
            # Optionally save debug images
            save_images = input("\n💾 Save debug images to 'debug_output' folder? (y/n): ").lower().strip()
            if save_images == 'y':
                pipeline.save_debug_images("debug_output")
                print("✅ Debug images saved!")
            
            return True
        else:
            print(f"\n❌ Pipeline failed: {results.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        return False
    finally:
        # Clean up
        if 'pipeline' in locals():
            pipeline.cleanup()

def test_individual_debug_features():
    """Test individual debug visualization features."""
    print("\n🧪 Testing Individual Debug Features")
    print("=" * 40)
    
    try:
        from debug_visualizer import DebugVisualizer
        
        # Test debug visualizer creation
        visualizer = DebugVisualizer("Test Debug")
        print("✅ DebugVisualizer created successfully")
        
        # Test adding debug stages
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        visualizer.add_debug_stage("Test Stage", test_image, "Test description")
        print("✅ Debug stage added successfully")
        
        # Test debug summary
        summary = visualizer.create_debug_summary()
        print("✅ Debug summary created successfully")
        
        # Clean up
        visualizer.cleanup()
        print("✅ Debug visualizer cleaned up successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Individual debug test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Debug Visualization System")
    print("=" * 60)
    
    # Test individual debug features
    individual_success = test_individual_debug_features()
    
    if individual_success:
        print("\n🎉 Individual debug features test passed!")
        
        # Test full debug visualization
        debug_success = test_debug_visualization()
        
        if debug_success:
            print("\n🎉 Full debug visualization test passed!")
            print("\n✨ Debug visualization system is working correctly!")
            print("\n📖 Usage Examples:")
            print("   • Basic: pipeline = VerseDetectionPipeline(enable_debug_visualizer=True)")
            print("   • Show windows: pipeline.show_debug_visualization()")
            print("   • Save images: pipeline.save_debug_images('output_folder')")
            print("   • Get summary: print(pipeline.get_debug_summary())")
        else:
            print("\n💥 Full debug visualization test failed!")
    else:
        print("\n💥 Individual debug features test failed!")
    
    print("\nNote: Debug visualization provides comprehensive visual debugging")
    print("for each step of the verse detection process.")
