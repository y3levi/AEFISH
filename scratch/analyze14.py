import cv2
import numpy as np

img_path = r"C:/Users/yagol/.gemini/antigravity/brain/02cee701-bf5a-4a3b-8ac9-3376feae6a7c/.user_uploaded/media_1788203935958.png"
img = cv2.imread(img_path)
frame_h, frame_w = img.shape[:2]

hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# The ZONE is blue, the FISH is light blue.
# Let's find the DARK minigame bar background first!
# It is H=90-110, S=50-90, V=50-90
dark_lower = np.array([90, 50, 50])
dark_upper = np.array([110, 95, 100])
dark_mask = cv2.inRange(hsv, dark_lower, dark_upper)

contours, _ = cv2.findContours(dark_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
print("--- DARK BAR ---")
bar_box = None
for cnt in contours:
    x, y, w, h = cv2.boundingRect(cnt)
    area = cv2.contourArea(cnt)
    if w > frame_w * 0.5 and h > 20: # The bar is very wide
        print(f"FOUND DARK BAR: x={x}, y={y}, w={w}, h={h}, area={area}")
        bar_box = (x, y, w, h)

# If we know where the dark bar is, we can just crop the image to the bar!
# Then the Roblox water is excluded!
if bar_box:
    x, y, w, h = bar_box
    bar_crop = hsv[y:y+h, x:x+w]
    
    # ZONE
    zone_lower = np.array([90, 80, 100])
    zone_upper = np.array([110, 255, 255])
    zone_mask = cv2.inRange(bar_crop, zone_lower, zone_upper)
    # morphological close to merge
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3))
    zone_mask = cv2.morphologyEx(zone_mask, cv2.MORPH_CLOSE, kernel)
    
    z_contours, _ = cv2.findContours(zone_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    print("--- ZONE ---")
    for cnt in z_contours:
        zx, zy, zw, zh = cv2.boundingRect(cnt)
        zarea = cv2.contourArea(cnt)
        if zw > 20 and zh > 10:
            print(f"FOUND ZONE: x={zx+x}, y={zy+y}, w={zw}, h={zh}, area={zarea}")

    # FISH (Light blue / white)
    fish_lower = np.array([90, 40, 160])
    fish_upper = np.array([110, 200, 255])
    fish_mask = cv2.inRange(bar_crop, fish_lower, fish_upper)
    f_contours, _ = cv2.findContours(fish_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    print("--- FISH ---")
    for cnt in f_contours:
        fx, fy, fw, fh = cv2.boundingRect(cnt)
        farea = cv2.contourArea(cnt)
        if 10 < farea < 1000:
            print(f"FOUND FISH: x={fx+x}, y={fy+y}, w={fw}, h={fh}, area={farea}")
