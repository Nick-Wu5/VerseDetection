import os
from google.cloud import vision
from dotenv import load_dotenv
from verse_detector import BibleVerseDetector

# Load environment variables and force override
load_dotenv(override=True)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Initialize the Vision API client
client = vision.ImageAnnotatorClient()

# Load Bible page image
# IMAGE_PATH = "Photos/proverbs_31.jpeg"
# IMAGE_PATH = "Photos/proverbs_12.jpeg"
IMAGE_PATH = "Photos/proverbs_27.jpeg"
# IMAGE_PATH = "Photos/psalm_139.jpeg"

with open(IMAGE_PATH, 'rb') as image_file:
    content = image_file.read()
image = vision.Image(content=content)

# Perform OCR
response = client.document_text_detection(image=image)
annotation = response.full_text_annotation

# Initialize verse detector
detector = BibleVerseDetector()

# Get verse statistics with confidence filtering
stats = detector.get_verse_statistics(annotation.text, confidence_threshold=0.6)  # Increased from 0.5

print("=== OCR Results ===")
print(f"Total lines detected: {stats['total_lines']}")
print(f"Total verse blocks found: {stats['verse_blocks']}")
print(f"Valid verse numbers: {stats['valid_verse_blocks']}")
print(f"Invalid verse numbers: {stats['invalid_verse_blocks']}")
print(f"Validation rate: {stats['validation_rate']:.1%}")
print(f"High-confidence verses: {stats['high_confidence_blocks']}")
print(f"Low-confidence verses: {stats['low_confidence_blocks']}")
print(f"Average confidence: {stats['average_confidence']:.2f}")
print(f"Average high-confidence: {stats['average_high_confidence']:.2f}")

print("\n=== High-Confidence Verse Numbers ===")
for verse_num in stats['high_confidence_verse_numbers']:
    print(f"✅ {verse_num}")

if stats['low_confidence_verse_numbers']:
    print("\n=== Low-Confidence Verse Numbers (Filtered Out) ===")
    for verse_num in stats['low_confidence_verse_numbers']:
        print(f"⚠️  {verse_num}")

if stats['invalid_verse_numbers']:
    print("\n=== Invalid Verse Numbers (Rejected) ===")
    for verse_num in stats['invalid_verse_numbers']:
        print(f"❌ {verse_num}")

print("\n=== Filtered Bible Text (High-Confidence Only) ===")
print(stats['filtered_text'])

print("\n=== All Detected Text (Including Low-Confidence) ===")
print(stats['all_text'])

print("\n=== Raw OCR Text ===")
print(annotation.text)