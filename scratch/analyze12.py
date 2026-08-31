import cv2
import numpy as np

img_path = r"C:/Users/yagol/.gemini/antigravity/brain/02cee701-bf5a-4a3b-8ac9-3376feae6a7c/.user_uploaded/media_1788203935958.png"
img = cv2.imread(img_path)
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Pick a point in the dark background of the minigame bar, say x=500, y=30
print(f"Dark background HSV at (500, 30): {hsv[30, 500]}")
print(f"Dark background HSV at (700, 30): {hsv[30, 700]}")
