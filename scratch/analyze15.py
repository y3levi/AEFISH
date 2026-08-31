import cv2
import numpy as np

img_path = r"C:/Users/yagol/.gemini/antigravity/brain/02cee701-bf5a-4a3b-8ac9-3376feae6a7c/.user_uploaded/media_1788203935958.png"
img = cv2.imread(img_path)
frame_h, frame_w = img.shape[:2]

hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

lower = np.array([85, 40, 140])
upper = np.array([120, 255, 255])
mask = cv2.inRange(hsv, lower, upper)

# DO NOT use MORPH_CLOSE or MORPH_OPEN heavily, just find raw contours
contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

print("--- SINGLE MASK VALIDATION ---")
for cnt in contours:
    x, y, w, h = cv2.boundingRect(cnt)
    area = cv2.contourArea(cnt)
    
    # Is it the ZONE?
    if w > 20 and h > 10 and area > 500:
        if w < frame_w * 0.70: # Not the whole screen
            print(f"ZONE CANDIDATE: x={x}, y={y}, w={w}, h={h}, area={area}")

    # Is it the FISH?
    if 10 < area < 1000:
        ar = w / float(max(1, h))
        if 0.5 <= ar <= 2.0:
            print(f"FISH CANDIDATE: x={x}, y={y}, w={w}, h={h}, area={area}, ar={ar:.2f}")

