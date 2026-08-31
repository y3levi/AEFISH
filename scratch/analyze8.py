import cv2
import numpy as np

img_path = r"C:/Users/yagol/.gemini/antigravity/brain/02cee701-bf5a-4a3b-8ac9-3376feae6a7c/.user_uploaded/media_1788203935958.png"
img = cv2.imread(img_path)
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

lower = np.array([0, 0, 180])
upper = np.array([180, 40, 255])
mask = cv2.inRange(hsv, lower, upper)

# WITHOUT MORPH_OPEN
contours_raw, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

print("--- WITHOUT MORPH_OPEN ---")
for cnt in contours_raw:
    x, y, w, h = cv2.boundingRect(cnt)
    if 650 <= x <= 720 and 10 <= y <= 50:
        area = cv2.contourArea(cnt)
        print(f"RAW: x={x}, y={y}, w={w}, h={h}, area={area}, ar={w/float(max(1,h)):.2f}")

# WITH MORPH_OPEN
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
mask_open = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
contours_open, _ = cv2.findContours(mask_open, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

print("--- WITH MORPH_OPEN ---")
for cnt in contours_open:
    x, y, w, h = cv2.boundingRect(cnt)
    if 650 <= x <= 720 and 10 <= y <= 50:
        area = cv2.contourArea(cnt)
        print(f"OPEN: x={x}, y={y}, w={w}, h={h}, area={area}, ar={w/float(max(1,h)):.2f}")
