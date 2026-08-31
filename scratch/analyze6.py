import cv2
import numpy as np

img_path = r"C:/Users/yagol/.gemini/antigravity/brain/02cee701-bf5a-4a3b-8ac9-3376feae6a7c/.user_uploaded/media_1788203935958.png"
img = cv2.imread(img_path)
debug_img = img.copy()
frame_h, frame_w = img.shape[:2]

hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# ZONE
lower = np.array([85, 60, 60])
upper = np.array([135, 255, 255])
mask = cv2.inRange(hsv, lower, upper)
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3))
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

for cnt in contours:
    area = cv2.contourArea(cnt)
    if 30 <= area <= 40000:
        x, y, w, h = cv2.boundingRect(cnt)
        if h < int(frame_h * 0.10) or w > frame_w * 0.70:
            continue
        cv2.rectangle(debug_img, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(debug_img, "ZONE", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

# FISH
lower = np.array([0, 0, 200])
upper = np.array([180, 40, 255])
mask = cv2.inRange(hsv, lower, upper)
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

for i, cnt in enumerate(contours):
    area = cv2.contourArea(cnt)
    if 10 <= area <= 2500:
        x, y, w, h = cv2.boundingRect(cnt)
        aspect_ratio = float(w) / max(1, h)
        if 0.1 <= aspect_ratio <= 4.0:
            cv2.rectangle(debug_img, (x, y), (x+w, y+h), (0, 0, 255), 2)
            cv2.putText(debug_img, f"F{i}", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

cv2.imwrite("C:/Users/yagol/.gemini/antigravity/brain/02cee701-bf5a-4a3b-8ac9-3376feae6a7c/scratch/debug_final.png", debug_img)
print("Saved debug_final.png")
