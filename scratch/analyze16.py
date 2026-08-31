import cv2
import numpy as np

img_path = r"C:/Users/yagol/.gemini/antigravity/brain/02cee701-bf5a-4a3b-8ac9-3376feae6a7c/.user_uploaded/media_1788204815425.png"
img = cv2.imread(img_path)
frame_h, frame_w = img.shape[:2]

hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

lower = np.array([85, 40, 140])
upper = np.array([125, 255, 255])
mask = cv2.inRange(hsv, lower, upper)

contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

print("--- ZONE CANDIDATES ---")
for cnt in contours:
    area = cv2.contourArea(cnt)
    if area > 100:
        x, y, w, h = cv2.boundingRect(cnt)
        if h < max(3, int(frame_h * 0.05)) or w > frame_w * 0.75:
            continue
        if w > h * 2:
            print(f"ZONE: x={x}, y={y}, w={w}, h={h}, area={area}")

print("--- FISH CANDIDATES ---")
for cnt in contours:
    area = cv2.contourArea(cnt)
    if 10 <= area <= 2500:
        x, y, w, h = cv2.boundingRect(cnt)
        aspect_ratio = float(w) / max(1, h)
        if 0.5 <= aspect_ratio <= 2.5:
            print(f"FISH: x={x}, y={y}, w={w}, h={h}, area={area}, ar={aspect_ratio:.2f}")

