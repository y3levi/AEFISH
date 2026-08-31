import cv2
import numpy as np

img_path = r"C:/Users/yagol/.gemini/antigravity/brain/02cee701-bf5a-4a3b-8ac9-3376feae6a7c/.user_uploaded/media_1788203935958.png"
img = cv2.imread(img_path)

hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# FISH Mask (White)
fish_lower = np.array([0, 0, 200])
fish_upper = np.array([180, 40, 255])
fish_mask = cv2.inRange(hsv, fish_lower, fish_upper)
kernel_fish = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
fish_mask_morph = cv2.morphologyEx(fish_mask, cv2.MORPH_OPEN, kernel_fish)
cv2.imwrite("scratch/fish_mask.png", fish_mask_morph)

# ZONE Mask (Blue)
# Let's see what color the light blue zone actually is!
# Let's save the hsv channels to see
cv2.imwrite("scratch/hsv_h.png", hsv[:,:,0])
cv2.imwrite("scratch/hsv_s.png", hsv[:,:,1])
cv2.imwrite("scratch/hsv_v.png", hsv[:,:,2])

zone_lower = np.array([95, 80, 60])
zone_upper = np.array([135, 255, 255])
zone_mask = cv2.inRange(hsv, zone_lower, zone_upper)
kernel_zone = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3))
zone_mask_morph = cv2.morphologyEx(zone_mask, cv2.MORPH_CLOSE, kernel_zone)
cv2.imwrite("scratch/zone_mask.png", zone_mask_morph)

# Let's draw contours on original
debug_img = img.copy()
contours_fish, _ = cv2.findContours(fish_mask_morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
for cnt in contours_fish:
    x, y, w, h = cv2.boundingRect(cnt)
    if w >= 2 and h >= 2:
        cv2.rectangle(debug_img, (x, y), (x+w, y+h), (0, 0, 255), 2) # Red for fish

contours_zone, _ = cv2.findContours(zone_mask_morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
for cnt in contours_zone:
    x, y, w, h = cv2.boundingRect(cnt)
    cv2.rectangle(debug_img, (x, y), (x+w, y+h), (0, 255, 0), 2) # Green for zone

cv2.imwrite("scratch/debug_contours.png", debug_img)
print("Saved masks to scratch/")
