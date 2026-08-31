import cv2
import numpy as np

img_path = r"C:/Users/yagol/.gemini/antigravity/brain/02cee701-bf5a-4a3b-8ac9-3376feae6a7c/.user_uploaded/media_1788203935958.png"
img = cv2.imread(img_path)
frame_h, frame_w = img.shape[:2]

hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Combined mask
lower = np.array([85, 40, 60])
upper = np.array([135, 255, 255])
mask = cv2.inRange(hsv, lower, upper)

# Use simple CLOSE to connect parts of the zone, but small kernel so we don't merge fish and zone
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

zone_cnt = None
fish_cnt = None

for cnt in contours:
    x, y, w, h = cv2.boundingRect(cnt)
    area = cv2.contourArea(cnt)
    
    # Is it the ZONE?
    if area > 100:
        # Zone is wide, height is decent percentage of frame
        if h >= max(4, int(frame_h * 0.10)) and w > 20 and w < frame_w * 0.70:
            if w > h * 2: # it's wide
                print(f"FOUND ZONE: x={x}, y={y}, w={w}, h={h}, area={area}")
                zone_cnt = cnt
                continue

    # Is it the FISH?
    if 10 <= area <= 2000:
        aspect_ratio = float(w) / max(1, h)
        # Fish is roughly square
        if 0.5 <= aspect_ratio <= 2.0:
            print(f"FOUND FISH: x={x}, y={y}, w={w}, h={h}, area={area}, ar={aspect_ratio:.2f}")
            fish_cnt = cnt

