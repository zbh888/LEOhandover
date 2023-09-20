import os
import sys

from PIL import Image


def get_numeric_value(filename):
    return int(filename.split('_')[-1].split('.')[0])


# Create an animation
def draw_animation(image_directory):
    image_files = [f"{image_directory}/{file}" for file in sorted(os.listdir(image_directory), key=get_numeric_value) if
                   file.lower().endswith((".png", ".jpg", ".jpeg"))]
    # print(image_files) # debug purpose
    images = [Image.open(file) for file in image_files]
    gif_path = f"{image_directory}/animation.gif"
    images[0].save(gif_path, save_all=True, append_images=images[1:], loop=0, duration=200)  # Adjust duration as needed


# python3 animation.py res
draw_animation(sys.argv[1])
