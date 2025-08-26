#!/usr/bin/env python3
"""
Comprehensive test script for the enhanced verse detection system.
Tests noise reduction, verse grouping, and debug visualization.
"""

import os
from verse_detection_pipeline import VerseDetectionPipeline

def test_comprehensive_system():
    """Test the complete enhanced system."""
    print("🧪 Testing Enhanced Verse Detection System")
    print("=" * 60)
    
    # Check authentication
    if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
        print("❌ GOOGLE_APPLICATION_CREDENTIALS not set")
        return False
    
    # Test images
    test_images = [
        "Photos/matthew_5(16-25).jpeg",  # Tests verse grouping
        "Photos/matthew_4(6-17).jpeg"    # Tests noise reduction
    ]
    
    for image_path in test_images:
        if not os.path.exists(image_path):
            print(f"⚠️  Image not found: {image_path}")
            continue
            
        print(f"\n📸 Testing with: {image_path}")
        print("-" * 50)
        
        # Create pipeline with debug visualization
        pipeline = VerseDetectionPipeline(
            show_visual_steps=True,
            enable_debug_visualizer=True
        )
        
        # Process image
        results = pipeline.process_image(image_path)
        
        if results['success']:
            print(f"✅ Processing successful!")
            print(f"📏 Underlines detected: {results['underlines_detected']}")
            print(f"📝 Text regions with content: {results['text_regions_extracted']}")
            print(f"📖 Verses detected: {results['verses_detected']}")
            
            if results['verses']:
                print("\n📖 Detected Verses:")
                for i, verse in enumerate(results['verses'], 1):
                    print(f"   {i}. {verse.verse_number}: {verse.content[:50]}...")
                    print(f"      Underlines: {verse.underline_indices}")
            
            # Show debug visualization
            print("\n🔍 Showing debug visualization...")
            pipeline.show_debug_visualization()
            
            # Save debug images
            print("\n💾 Saving debug images...")
            output_dir = f"debug_{os.path.basename(image_path).split('.')[0]}"
            pipeline.save_debug_images(output_dir)
            
        else:
            print(f"❌ Processing failed: {results.get('error', 'Unknown error')}")
        
        # Cleanup
        pipeline.cleanup()
    
    return True

if __name__ == "__main__":
    success = test_comprehensive_system()
    if success:
        print("\n🎉 Comprehensive test completed successfully!")
    else:
        print("\n💥 Comprehensive test failed!")
