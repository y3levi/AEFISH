import cv2
import numpy as np

img_path = r"C:/Users/yagol/.gemini/antigravity/brain/02cee701-bf5a-4a3b-8ac9-3376feae6a7c/.user_uploaded/media_1788203935958.png"
img = cv2.imread(img_path)
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Raise V minimum to 120 to ignore dark blue background
lower = np.array([85, 40, 120])
upper = np.array([135, 255, 255])
mask = cv2.inRange(hsv, lower, upper)

contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

print("--- CONTOURS IN STRICTER MASK ---")
for cnt in contours:
    x, y, w, h = cv2.boundingRect(cnt)
    area = cv2.contourArea(cnt)
    if area > 10:
        print(f"x={x}, y={y}, w={w}, h={h}, area={area}, ar={w/max(1,h):.2f}")
