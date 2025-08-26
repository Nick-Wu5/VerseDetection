#!/usr/bin/env python3
"""
Simple example showing how to use debug visualization.
This demonstrates the visual debugging capabilities.
"""

from verse_detection_pipeline import VerseDetectionPipeline

def main():
    """Demonstrate debug visualization usage."""
    
    print("🔍 Debug Visualization Example")
    print("=" * 40)
    
    # Create pipeline with debug visualizer enabled
    print("Creating pipeline with debug visualizer...")
    pipeline = VerseDetectionPipeline(
        show_visual_steps=False,  # Disable old visual steps
        enable_debug_visualizer=True  # Enable new debug visualizer
    )
    
    # Process an image
    print("Processing image...")
    results = pipeline.process_image("Photos/matthew_5(16-25).jpeg")
    
    if results['success']:
        print("✅ Processing successful!")
        
        # Show debug summary
        print("\n📊 Debug Summary:")
        print(pipeline.get_debug_summary())
        
        # Show all debug visualization windows
        print("\n🖼️  Showing debug visualization...")
        print("You should see multiple windows:")
        print("  • Text Mask - Binary mask after preprocessing")
        print("  • Detected Underlines - Underlines with numbering")
        print("  • Text Extraction Regions - Highlighted regions")
        print("  • Verse Blocks - Color-coded verse groups")
        
        # Display all debug windows
        pipeline.show_debug_visualization(wait_for_key=True)
        
        # Save debug images (optional)
        print("\n💾 Saving debug images...")
        pipeline.save_debug_images("debug_example_output")
        
    else:
        print(f"❌ Processing failed: {results.get('error', 'Unknown error')}")
    
    # Clean up
    pipeline.cleanup()

if __name__ == "__main__":
    main()
