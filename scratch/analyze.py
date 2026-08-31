import cv2
import numpy as np
import sys

img_path = r"C:/Users/yagol/.gemini/antigravity/brain/02cee701-bf5a-4a3b-8ac9-3376feae6a7c/.user_uploaded/media_1788203935958.png"
img = cv2.imread(img_path)
if img is None:
    print("Failed to load image")
    sys.exit(1)

print(f"Image shape: {img.shape}")

hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# FISH Mask (White)
fish_lower = np.array([0, 0, 200])
fish_upper = np.array([180, 40, 255])
fish_mask = cv2.inRange(hsv, fish_lower, fish_upper)
kernel_fish = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
fish_mask_morph = cv2.morphologyEx(fish_mask, cv2.MORPH_OPEN, kernel_fish)

contours, _ = cv2.findContours(fish_mask_morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
print(f"--- FISH CONTOURS ---")
for i, cnt in enumerate(contours):
    x, y, w, h = cv2.boundingRect(cnt)
    area = cv2.contourArea(cnt)
    ar = w / float(max(1, h))
    print(f"Contour {i}: x={x}, y={y}, w={w}, h={h}, area={area}, ar={ar:.2f}")

# ZONE Mask (Blue)
zone_lower = np.array([95, 80, 60])
zone_upper = np.array([135, 255, 255])
zone_mask = cv2.inRange(hsv, zone_lower, zone_upper)
kernel_zone = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3))
zone_mask_morph = cv2.morphologyEx(zone_mask, cv2.MORPH_CLOSE, kernel_zone)

contours_zone, _ = cv2.findContours(zone_mask_morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
print(f"--- ZONE CONTOURS ---")
for i, cnt in enumerate(contours_zone):
    x, y, w, h = cv2.boundingRect(cnt)
    area = cv2.contourArea(cnt)
    print(f"Contour {i}: x={x}, y={y}, w={w}, h={h}, area={area}")

