# Verse Detection System

A modular, professional-grade system for detecting and extracting Bible verses from underlined text in images.

## 🚀 Features

- **Modular Architecture**: Clean, maintainable code structure
- **Advanced Underline Detection**: Sophisticated filtering and noise reduction
- **OCR Text Extraction**: Google Cloud Vision API integration
- **Verse Processing**: Intelligent verse detection and grouping
- **Comprehensive Debugging**: Visual debugging at every processing stage
- **Professional Quality**: Production-ready code with proper error handling

## 🏗️ Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                    VerseDetectionPipeline                   │
│                     (Main Orchestrator)                    │
└─────────────────┬───────────────────────────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
┌───▼───┐   ┌────▼────┐   ┌────▼────┐
│Image  │   │Underline│   │  Text   │
│Preproc│   │Detector │   │Extractor│
└───────┘   └─────────┘   └─────────┘
    │             │             │
    └─────────────┼─────────────┘
                  │
            ┌─────▼────┐
            │  Verse   │
            │Processor │
            └──────────┘
```

## 📦 Modules

### **ImagePreprocessor** (`image_preprocessor.py`)

- Image loading and validation
- Noise reduction with bilateral filtering
- Binary text mask creation
- Clean interfaces for other modules

### **UnderlineDetector** (`underline_detector_module.py`)

- Morphological underline detection
- Noise filtering and line validation
- Segment merging for complete underlines
- Visualization capabilities

### **TextExtractor** (`text_extractor.py`)

- OCR text extraction from image regions
- Context expansion for complete verses
- Text cleaning and artifact removal
- Google Cloud Vision API integration

### **VerseProcessor** (`verse_processor.py`)

- Verse number pattern detection
- Proximity-based verse grouping
- Quality analysis and confidence scoring
- Verse block management

### **DebugVisualizer** (`debug_visualizer.py`)

- Comprehensive visual debugging
- Stage-by-stage visualization
- Debug image saving
- Professional debugging tools

### **VerseDetectionPipeline** (`verse_detection_pipeline.py`)

- Main orchestration and coordination
- Error handling and result aggregation
- Debug visualization integration
- Clean user interface

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- OpenCV (cv2)
- NumPy
- Google Cloud Vision API credentials

### Setup

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd VerseDetection
   ```

2. **Create virtual environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Google Cloud Vision API**

   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"
   ```

## 🚀 Usage

### Basic Usage

```python
from verse_detection_pipeline import VerseDetectionPipeline

# Create pipeline
pipeline = VerseDetectionPipeline()

# Process image
results = pipeline.process_image("Photos/matthew_5(16-25).jpeg")

# Check results
if results['success']:
    print(f"Detected {results['verses_detected']} verses")
    for verse in results['verses']:
        print(f"{verse.verse_number}: {verse.content}")
```

### Debug Mode

```python
# Enable comprehensive debugging
pipeline = VerseDetectionPipeline(enable_debug_visualizer=True)

# Process image with debug capture
results = pipeline.process_image("image.jpg")

# Show debug visualization
pipeline.show_debug_visualization()

# Save debug images
pipeline.save_debug_images("debug_output")
```

### Individual Module Usage

```python
from image_preprocessor import ImagePreprocessor
from underline_detector_module import UnderlineDetector

# Use individual modules
preprocessor = ImagePreprocessor()
preprocessor.load_image("image.jpg")
gray = preprocessor.preprocess_image()
text_mask = preprocessor.create_text_mask(gray)

detector = UnderlineDetector()
underlines = detector.detect_underlines(text_mask, width)
```

## 🧪 Testing

### Run Complete Pipeline Test

```bash
python test_modular_pipeline.py
```

### Run Debug Visualization Test

```bash
python test_debug_visualization.py
```

### Run Simple Example

```bash
python debug_example.py
```

### Test Individual Modules

```bash
# Test image preprocessing
python -c "from image_preprocessor import ImagePreprocessor; print('✅ ImagePreprocessor works')"

# Test underline detection
python -c "from underline_detector_module import UnderlineDetector; print('✅ UnderlineDetector works')"

# Test text extraction
python -c "from text_extractor import TextExtractor; print('✅ TextExtractor works')"

# Test verse processing
python -c "from verse_processor import VerseProcessor; print('✅ VerseProcessor works')"

# Test debug visualizer
python -c "from debug_visualizer import DebugVisualizer; print('✅ DebugVisualizer works')"
```

## 🔍 Debug Visualization

The system provides comprehensive visual debugging:

### **Debug Windows**

1. **Text Mask**: Binary mask after preprocessing
2. **Detected Underlines**: Numbered underlines with coordinates
3. **Text Extraction Regions**: Highlighted text regions
4. **Verse Blocks**: Color-coded verse groups

### **Debug Features**

- **Stage-by-stage visualization** of processing steps
- **Numbered underlines** for easy reference
- **Color-coded verse groups** for clarity
- **Debug image saving** for analysis
- **Text summaries** of debug stages

### **Enable Debug Mode**

```python
pipeline = VerseDetectionPipeline(enable_debug_visualizer=True)
pipeline.show_debug_visualization()
pipeline.save_debug_images("debug_output")
```

## 📊 Output

### **Results Structure**

```python
{
    'success': True,
    'underlines_detected': 13,
    'text_regions_extracted': 15,
    'verses_detected': 8,
    'analysis': {
        'total_verses': 8,
        'average_confidence': 0.85,
        'completeness_score': 0.92,
        'quality_issues': []
    },
    'verses': [VerseBlock, ...],
    'extracted_text': {...}
}
```

### **VerseBlock Structure**

```python
VerseBlock(
    text="25 'Settle matters quickly with your adversary...'",
    verse_number="25",
    content="'Settle matters quickly with your adversary...'",
    underline_indices=[3, 4, 5],
    confidence=0.92,
    y_position=2638
)
```

## 🎯 Key Benefits

### **✅ Maintainability**

- Clean separation of concerns
- Easy to modify individual components
- Clear interfaces between modules

### **✅ Testability**

- Each module can be tested independently
- Mock objects can replace dependencies
- Comprehensive test coverage

### **✅ Debugging**

- Visual debugging at every stage
- Professional debugging tools
- Easy issue isolation

### **✅ Extensibility**

- Easy to add new modules
- Plugin architecture possible
- Future-ready design

## 🚧 Troubleshooting

### Common Issues

1. **Import Errors**

   - Ensure all modules are in the same directory
   - Check Python path and virtual environment

2. **Authentication Errors**

   - Verify `GOOGLE_APPLICATION_CREDENTIALS` environment variable
   - Check service account key file path

3. **Image Loading Errors**

   - Verify image file paths and formats
   - Check file permissions

4. **Memory Issues**
   - Large images may require more memory
   - Consider image resizing for very large files

### Enable Debug Visualization

Enable debug visualization to see exactly what's happening at each step:

```python
pipeline = VerseDetectionPipeline(enable_debug_visualizer=True)
```

## 🔮 Future Enhancements

### **Potential New Modules**

- **VerseValidator**: Validate against reference texts
- **OutputFormatter**: Multiple output formats (JSON, CSV, etc.)
- **BatchProcessor**: Process multiple images
- **QualityAssessor**: Advanced quality algorithms

### **Integration Possibilities**

- **Web Interface**: Flask/FastAPI wrapper
- **Database Storage**: Save results for analysis
- **Machine Learning**: ML-based improvements
- **Cloud Deployment**: Microservices architecture

## 📝 License

[Add your license information here]

## 🤝 Contributing

[Add contribution guidelines here]

## 📞 Support

[Add support contact information here]

---

## 🎉 Built with ❤️ for Bible verse detection and analysis
