import cv2
import numpy as np
import os

img_path = r"C:/Users/yagol/.gemini/antigravity/brain/02cee701-bf5a-4a3b-8ac9-3376feae6a7c/.user_uploaded/media_1788203935958.png"
img = cv2.imread(img_path)

# The fish is located around x=685, y=20, w=24, h=24. Let's crop a bit larger.
fish_crop = img[22:42, 687:707]

out_path = "assets/fish_template.png"
cv2.imwrite(out_path, fish_crop)
print(f"Saved template to {out_path}")
