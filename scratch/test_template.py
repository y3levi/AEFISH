import cv2
import numpy as np

img_path = r"C:/Users/yagol/.gemini/antigravity/brain/02cee701-bf5a-4a3b-8ac9-3376feae6a7c/.user_uploaded/media_1788203935958.png"
img = cv2.imread(img_path)
template = cv2.imread("assets/fish_template.png")

res = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

print(f"Template match max value: {max_val:.3f} at {max_loc}")

if max_val > 0.7:
    debug_img = img.copy()
    h, w = template.shape[:2]
    cv2.rectangle(debug_img, max_loc, (max_loc[0] + w, max_loc[1] + h), (0, 0, 255), 2)
    cv2.imwrite("scratch/template_match.png", debug_img)
