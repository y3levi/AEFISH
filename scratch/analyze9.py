import cv2
import numpy as np

img_path = r"C:/Users/yagol/.gemini/antigravity/brain/02cee701-bf5a-4a3b-8ac9-3376feae6a7c/.user_uploaded/media_1788203935958.png"
img = cv2.imread(img_path)
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# The fish is around x=689, y=24, w=16, h=18
fish_crop = hsv[24:24+18, 689:689+16]
print("FISH HSV values:")
for y in range(fish_crop.shape[0]):
    for x in range(fish_crop.shape[1]):
        h, s, v = fish_crop[y, x]
        if v > 100: # Ignore pure black outline
            print(f"H={h}, S={s}, V={v}")
