import cv2 as cv
import numpy as np

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

IMAGE_PATH = "Photos/proverbs_27(4-23).jpeg"

img = cv.imread(IMAGE_PATH)
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
else:
    print("No underlines detected")
    cv.imshow("Detected Underlines", result_img)

print("Press any key to close")
cv.waitKey(0)
cv.destroyAllWindows()