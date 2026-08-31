import cv2
import numpy as np

img_path = r"C:/Users/yagol/.gemini/antigravity/brain/02cee701-bf5a-4a3b-8ac9-3376feae6a7c/.user_uploaded/media_1788203935958.png"
img = cv2.imread(img_path)
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

lower = np.array([0, 0, 150]) # Lower V to catch dimmer white
upper = np.array([180, 50, 255])
mask = cv2.inRange(hsv, lower, upper)

contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

print("--- ALL WHITE CONTOURS in X: 600-750 ---")
for i, cnt in enumerate(contours):
    x, y, w, h = cv2.boundingRect(cnt)
    if 600 <= x <= 750:
        area = cv2.contourArea(cnt)
        print(f"Contour {i}: x={x}, y={y}, w={w}, h={h}, area={area}, ar={w/float(max(1,h)):.2f}")
