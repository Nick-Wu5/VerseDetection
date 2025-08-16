import cv2 as cv
import numpy as np

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
# Since underlines are already visible in text mask, use horizontal erosion to isolate them
underline_mask = np.zeros_like(text_mask)
k_heights = [1, 2, 3]  # Different underline thicknesses
k_widths = [max(15, width//60), max(25, width//40), max(35, width//30)]  # Different underline lengths

for ky in k_heights:
    for kx in k_widths:
        # Use horizontal kernel to erode text and isolate horizontal lines
        kernel = cv.getStructuringElement(cv.MORPH_RECT, (kx, ky))
        # Erode the text mask to isolate horizontal structures (underlines)
        eroded = cv.erode(text_mask, kernel)
        underline_mask = np.maximum(underline_mask, eroded)

cv.imshow("Underline Mask", underline_mask)

# 4) Clean up underline mask to remove noise
# Use horizontal closing to connect broken underline segments
kernel_clean = cv.getStructuringElement(cv.MORPH_RECT, (max(20, width//50), 1))
underline_clean = cv.morphologyEx(underline_mask, cv.MORPH_CLOSE, kernel_clean)
cv.imshow("Cleaned Underlines", underline_clean)

# 5) Use Probabilistic Hough Line Transform with strict parameters
underline_binary_uint8 = np.uint8(underline_clean)

lines = cv.HoughLinesP(underline_binary_uint8, 
                       rho=1,
                       theta=np.pi/180,
                       threshold=80,  # Lower threshold to catch more lines
                       minLineLength=max(50, width//20),  # Shorter minimum length to catch shorter lines
                       maxLineGap=25)  # Larger gap to connect broken segments

# 6) Filter and draw detected lines
result_img = img.copy()
if lines is not None:
    horizontal_lines = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        if x2 - x1 != 0:
            angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
            # Keep only very horizontal lines (±5 degrees)
            if abs(angle) < 5 or abs(angle - 180) < 5:
                line_length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                # Must be at least 25% of image width
                if line_length > width * 0.1:
                    horizontal_lines.append(line)
    
    # Draw detected underlines
    for line in horizontal_lines:
        x1, y1, x2, y2 = line[0]
        cv.line(result_img, (x1, y1), (x2, y2), (0, 255, 0), 3)
    
    cv.imshow("Detected Underlines", result_img)
    print(f"Detected {len(horizontal_lines)} underlines")
else:
    print("No underlines detected")
    cv.imshow("Detected Underlines", result_img)

print("Press any key to close")
cv.waitKey(0)
cv.destroyAllWindows()