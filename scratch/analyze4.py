import cv2
import numpy as np

img_path = r"C:/Users/yagol/.gemini/antigravity/brain/02cee701-bf5a-4a3b-8ac9-3376feae6a7c/.user_uploaded/media_1788203935958.png"
img = cv2.imread(img_path)

hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Print HSV values at specific coordinates that look like the blue bar
# Looking at the image, the blue bar is roughly in the lower middle.
# Let's just print max/min hue for pixels that are bright blue
blue_pixels = []
for y in range(img.shape[0]):
    for x in range(img.shape[1]):
        b, g, r = img[y, x]
        if b > 150 and g > 100 and r < 100: # rough guess for light blue
            blue_pixels.append(hsv[y, x])

if blue_pixels:
    blue_pixels = np.array(blue_pixels)
    print(f"Blue pixels found: {len(blue_pixels)}")
    print(f"H min/max: {blue_pixels[:,0].min()} - {blue_pixels[:,0].max()}")
    print(f"S min/max: {blue_pixels[:,1].min()} - {blue_pixels[:,1].max()}")
    print(f"V min/max: {blue_pixels[:,2].min()} - {blue_pixels[:,2].max()}")

# Also, let's find the white progress bar
white_pixels = []
for y in range(img.shape[0]):
    for x in range(img.shape[1]):
        b, g, r = img[y, x]
        if b > 230 and g > 230 and r > 230:
            white_pixels.append(hsv[y, x])

if white_pixels:
    white_pixels = np.array(white_pixels)
    print(f"White pixels found: {len(white_pixels)}")
    print(f"H min/max: {white_pixels[:,0].min()} - {white_pixels[:,0].max()}")
    print(f"S min/max: {white_pixels[:,1].min()} - {white_pixels[:,1].max()}")
    print(f"V min/max: {white_pixels[:,2].min()} - {white_pixels[:,2].max()}")

