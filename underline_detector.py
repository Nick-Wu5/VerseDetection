import cv2 as cv
import numpy as np
from google.cloud import vision
from typing import List, Dict, Tuple
import os
import sys

def check_google_vision_auth():
    """Check if Google Cloud Vision API authentication is properly configured."""
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if not credentials_path:
        print("❌ GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
        print("Please set it to your service account key file path:")
        print("export GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/key.json")
        return False
    
    if not os.path.exists(credentials_path):
        print(f"❌ Credentials file not found: {credentials_path}")
        return False
    
    try:
        # Test the client
        client = vision.ImageAnnotatorClient()
        print("✅ Google Cloud Vision API authentication successful")
        return True
    except Exception as e:
        print(f"❌ Error authenticating with Google Cloud Vision API: {e}")
        return False

def merge_line_group(line_group):
    """Merge a group of close line segments into a single line."""
    if len(line_group) == 1:
        return line_group[0]
    
    # Find the bounding box of all lines in the group
    all_x = []
    all_y = []
    
    for line in line_group:
        x1, y1, x2, y2 = line[0]
        all_x.extend([x1, x2])
        all_y.extend([y1, y2])
    
    # Calculate the merged line
    x_min, x_max = min(all_x), max(all_x)
    y_avg = int(sum(all_y) / len(all_y))  # Convert to int for cv.line
    
    # Return a single line spanning the full width
    return np.array([[x_min, y_avg, x_max, y_avg]])

def merge_nearby_segments(lines, y_threshold=15, x_gap=50):
    """Merge line segments that are close vertically and horizontally."""
    if len(lines) <= 1:
        return lines
    
    # Sort by y-coordinate first
    lines.sort(key=lambda line: line[0][1])
    
    merged = []
    current_group = [lines[0]]
    
    for line in lines[1:]:
        x1, y1, x2, y2 = line[0]
        prev_line = current_group[-1]
        prev_x1, prev_y1, prev_x2, prev_y2 = prev_line[0]
        
        # Check if lines are close vertically AND horizontally
        y_close = abs(y1 - prev_y1) <= y_threshold
        
        # Check if lines could form a continuous underline
        x_overlap = (x1 <= prev_x2 + x_gap) and (prev_x1 <= x2 + x_gap)
        
        if y_close and x_overlap:
            current_group.append(line)
        else:
            # Merge current group and start new one
            merged.append(merge_line_group(current_group))
            current_group = [line]
    
    # Don't forget the last group
    if current_group:
        merged.append(merge_line_group(current_group))
    
    return merged

def get_text_above_underlines(underlines: List, original_image: np.ndarray, search_height: int = 50) -> Dict[int, str]:
    """
    Extract text regions above each detected underline using Google Cloud Vision API.
    
    Args:
        underlines: List of detected underline coordinates [(x1, y1, x2, y2), ...]
        original_image: Original BGR image for OCR processing
        search_height: Vertical distance above underline to search for text (default: 50px)
    
    Returns:
        Dictionary mapping underline index to extracted text
    """
    text_regions = {}
    
    # Initialize Google Cloud Vision client
    client = vision.ImageAnnotatorClient()
    
    for i, line in enumerate(underlines):
        x1, y1, x2, y2 = line[0]
        y_underline = int(y1)  # y-coordinate of the underline
        
        # Define search region above the underline
        y_start = max(0, y_underline - search_height)
        y_end = y_underline
        
        # Extract text region above this underline from original image
        text_region = original_image[y_start:y_end, x1:x2]
        
        try:
            # Convert BGR to RGB (Google Cloud Vision expects RGB)
            text_region_rgb = cv.cvtColor(text_region, cv.COLOR_BGR2RGB)
            
            # Convert to bytes for Google Cloud Vision API
            success, buffer = cv.imencode('.png', text_region_rgb)
            if not success:
                print(f"Error encoding image for underline {i}")
                text_regions[i] = ""
                continue
                
            image_bytes = buffer.tobytes()
            
            # Create image object for Google Cloud Vision
            image = vision.Image(content=image_bytes)
            
            # Perform text detection
            response = client.text_detection(image=image)
            
            # Check for API errors
            if hasattr(response, 'error') and response.error.message:
                print(f"Underline {i}: Google Cloud Vision API error: {response.error.message}")
                text_regions[i] = ""
                continue
                
            texts = response.text_annotations
            
            if texts:
                # Get the first (and usually only) text annotation
                extracted_text = texts[0].description.strip()
                if extracted_text:
                    text_regions[i] = extracted_text
                    print(f"Underline {i}: Found text '{extracted_text}' above underline at y={y_underline}")
                else:
                    print(f"Underline {i}: No text found above underline at y={y_underline}")
                    text_regions[i] = ""
            else:
                print(f"Underline {i}: No text detected above underline at y={y_underline}")
                text_regions[i] = ""
                
        except Exception as e:
            print(f"Error extracting text for underline {i}: {e}")
            text_regions[i] = ""
    
    return text_regions

# Check Google Cloud Vision API authentication first
if not check_google_vision_auth():
    print("\n❌ Cannot proceed without proper Google Cloud Vision API authentication.")
    print("Please follow the setup instructions and try again.")
    sys.exit(1)

IMAGE_PATH = "Photos/proverbs_27(4-23).jpeg"

img = cv.imread(IMAGE_PATH)
if img is None:
    print(f"❌ Error: Could not load image from {IMAGE_PATH}")
    sys.exit(1)
    
height, width = img.shape[:2]

# 1) Prep
gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
cv.imshow("Grayscale", gray)

# Apply bilateral filter to reduce noise while preserving edges
gray = cv.bilateralFilter(gray, 9, 75, 75)
cv.imshow("After Bilateral Filter", gray)

# 2) Create text mask to isolate text regions
text_mask = cv.adaptiveThreshold(gray, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                cv.THRESH_BINARY_INV, 11, 2)
cv.imshow("Text Mask", text_mask)

# Clean up text mask
kernel = cv.getStructuringElement(cv.MORPH_RECT, (3, 3))
text_mask = cv.morphologyEx(text_mask, cv.MORPH_CLOSE, kernel)
text_mask = cv.morphologyEx(text_mask, cv.MORPH_OPEN, kernel)
cv.imshow("Cleaned Text Mask", text_mask)

# 3) Extract underlines directly from text mask using horizontal kernels
underline_mask = np.zeros_like(text_mask)
k_heights = [1, 2, 3]  # Different underline thicknesses
k_widths = [max(10, width//80), max(20, width//60), max(30, width//40)]  # Thinner kernels

for ky in k_heights:
    for kx in k_widths:
        kernel = cv.getStructuringElement(cv.MORPH_RECT, (kx, ky))
        eroded = cv.erode(text_mask, kernel)
        underline_mask = np.maximum(underline_mask, eroded)

cv.imshow("Underline Mask", underline_mask)

# 4) Clean up underline mask to remove noise
kernel_clean = cv.getStructuringElement(cv.MORPH_RECT, (max(20, width//50), 1))
underline_clean = cv.morphologyEx(underline_mask, cv.MORPH_CLOSE, kernel_clean)
cv.imshow("Cleaned Underlines", underline_clean)

# 5) Use Probabilistic Hough Line Transform with strict parameters
underline_binary_uint8 = np.uint8(underline_clean)

lines = cv.HoughLinesP(underline_binary_uint8, 
                       rho=1,
                       theta=np.pi/180,
                       threshold=70,  # Lower threshold to catch more lines
                       minLineLength=max(50, width//20),  # Shorter minimum length to catch shorter lines
                       maxLineGap=35)  # Larger gap to connect broken segments

# 6) Filter and draw detected lines
result_img = img.copy()
if lines is not None:
    horizontal_lines = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        if x2 - x1 != 0:
            angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
            # Keep only very horizontal lines (±5 degrees)
            if abs(angle) < 10 or abs(angle - 180) < 10:
                line_length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                # Must be at least 10% of image width
                if line_length > width * 0.05:
                    horizontal_lines.append(line)
    
    # 7) Merge nearby segments into single underline intentions
    if len(horizontal_lines) > 1:
        horizontal_lines = merge_nearby_segments(horizontal_lines, y_threshold=15, x_gap=50)
    
    # Draw detected underlines
    for line in horizontal_lines:
        x1, y1, x2, y2 = line[0]
        # Ensure coordinates are integers
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        cv.line(result_img, (x1, y1), (x2, y2), (0, 255, 0), 3)
    
    cv.imshow("Detected Underlines", result_img)
    print(f"Detected {len(horizontal_lines)} underlines")
    
    # Phase 1: Extract text above underlines
    print("\n=== Phase 1: Extracting Text Above Underlines ===")
    text_regions = get_text_above_underlines(horizontal_lines, img)
    
    if text_regions:
        print(f"\nExtracted text from {len(text_regions)} underlines:")
        for underline_idx, text in text_regions.items():
            print(f"  Underline {underline_idx}: '{text}'")
    else:
        print("No text extracted from underlines")
        
else:
    print("No underlines detected")
    cv.imshow("Detected Underlines", result_img)

print("\nPress any key to close")
cv.waitKey(0)
cv.destroyAllWindows()