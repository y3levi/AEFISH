import cv2
import numpy as np

img_path = r"C:/Users/yagol/.gemini/antigravity/brain/02cee701-bf5a-4a3b-8ac9-3376feae6a7c/.user_uploaded/media_1788203935958.png"
img = cv2.imread(img_path)
frame_h, frame_w = img.shape[:2]

hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# FISH
lower = np.array([0, 0, 200])
upper = np.array([180, 40, 255])
min_area = 8
max_area = 2500
mask = cv2.inRange(hsv, lower, upper)
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

min_ar = 0.1
max_ar = 4.0

print(f"--- FISH VALIDATION (Frame: {frame_w}x{frame_h}) ---")
for cnt in contours:
    area = cv2.contourArea(cnt)
    if min_area <= area <= max_area:
        x, y, w, h = cv2.boundingRect(cnt)
        if w < 2 or h < 2 or w > frame_w * 0.35:
            print(f"REJECTED bounds: {w}x{h} for area {area}")
            continue
        aspect_ratio = float(w) / max(1, h)
        if min_ar <= aspect_ratio <= max_ar:
            print(f"ACCEPTED: x={x}, y={y}, w={w}, h={h}, area={area}, ar={aspect_ratio:.2f}")
        else:
            print(f"REJECTED AR: {aspect_ratio:.2f} for area {area}")

# ZONE
lower = np.array([95, 80, 60])
upper = np.array([135, 255, 255])
min_area = 30
max_area = 40000
mask = cv2.inRange(hsv, lower, upper)
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3))
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

print(f"--- ZONE VALIDATION ---")
for cnt in contours:
    area = cv2.contourArea(cnt)
    if min_area <= area <= max_area:
        x, y, w, h = cv2.boundingRect(cnt)
        if h < max(4, int(frame_h * 0.25)) or w > frame_w * 0.70:
            print(f"REJECTED bounds: {w}x{h} (req h>={max(4, int(frame_h * 0.25))}, w<={frame_w * 0.70}) for area {area}")
            continue
        print(f"ACCEPTED: x={x}, y={y}, w={w}, h={h}, area={area}")

