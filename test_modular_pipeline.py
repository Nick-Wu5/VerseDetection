#!/usr/bin/env python3
"""
Test script for the modular verse detection pipeline.
Demonstrates the new modular architecture.
"""

import os
from verse_detection_pipeline import VerseDetectionPipeline

def test_modular_pipeline():
    """Test the new modular verse detection pipeline."""
    
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
    
    print("🧪 Testing Modular Verse Detection Pipeline")
    print("=" * 60)
    
    try:
        # Create pipeline instance (without visual steps for testing)
        pipeline = VerseDetectionPipeline(show_visual_steps=False)
        
        # Process the image through the complete pipeline
        results = pipeline.process_image(IMAGE_PATH)
        
        if results['success']:
            print("\n✅ Pipeline test completed successfully!")
            
            # Display summary
            print(f"\n📊 Summary:")
            print(f"   • Underlines detected: {results['underlines_detected']}")
            print(f"   • Text regions extracted: {results['text_regions_extracted']}")
            print(f"   • Verses detected: {results['verses_detected']}")
            
            if results['verses_detected'] > 0:
                print(f"\n📖 Sample detected verses:")
                for i, verse in enumerate(results['verses'][:3]):  # Show first 3
                    print(f"   {i+1}. {verse.verse_number}: {verse.content[:80]}...")
            
            return True
        else:
            print(f"\n❌ Pipeline test failed: {results.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        return False
    finally:
        # Clean up
        if 'pipeline' in locals():
            pipeline.cleanup()

if __name__ == "__main__":
    print("Testing Modular Verse Detection Pipeline")
    print("=" * 60)
    
    success = test_modular_pipeline()
    
    if success:
        print("\n🎉 All tests passed! The modular system is working correctly.")
    else:
        print("\n💥 Some tests failed. Check the error messages above.")
    
    print("\nNote: This test runs without visual output for automated testing.")
    print("For visual debugging, set show_visual_steps=True in the pipeline.")
