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
IMAGE_PATH = "Photos/psalm_139.jpeg"
with open(IMAGE_PATH, 'rb') as image_file:
    content = image_file.read()
image = vision.Image(content=content)

# Perform OCR
response = client.document_text_detection(image=image)
annotation = response.full_text_annotation

# Initialize verse detector
detector = BibleVerseDetector()

# Get verse statistics and filtered text
stats = detector.get_verse_statistics(annotation.text)

print("=== OCR Results ===")
print(f"Total lines detected: {stats['total_lines']}")
print(f"Verse blocks found: {stats['verse_blocks']}")
print(f"Average confidence: {stats['average_confidence']:.2f}")

print("\n=== Detected Verse Numbers ===")
for verse_num in stats['verse_numbers']:
    print(f"- {verse_num}")

print("\n=== Filtered Bible Text (Main Content Only) ===")
print(stats['filtered_text'])

print("\n=== Raw OCR Text ===")
print(annotation.text)