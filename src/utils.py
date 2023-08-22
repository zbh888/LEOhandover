import random

import math
from PIL import Image
import matplotlib.pyplot as plt


# The number of devices requiring handover
def handout(R, N, d):
    pi = math.pi
    RES = N - 2 * N / pi * math.acos(d / 2 / R) + d * N / pi * (1 / R / R - (d * d) / (4 * R ** 4)) ** 0.5
    return RES


# uniform devices generator
def generate_points(n, R, x, y):
    def generate_one(R, x, y):
        r = R * math.sqrt(random.uniform(0, 1))
        theta = random.uniform(0, 1) * 2 * math.pi
        px = x + r * math.cos(theta)
        py = y + r * math.sin(theta)
        return px, py

    points = []
    for i in range(n):
        points.append(generate_one(R, x, y))
    return points


def draw_from_positions(total_positions, success_position, requested_position, label):
    unrequested_positions = [pos for pos in total_positions if pos not in success_position and pos not in requested_position]
    if len(unrequested_positions) != 0:
        x_coords, y_coords = zip(*unrequested_positions)
        plt.scatter(x_coords, y_coords, color='red', s=0.5)
    if len(success_position) != 0:
        x_coords, y_coords = zip(*success_position)
        plt.scatter(x_coords, y_coords, color='blue', s=0.5)
    if len(requested_position) != 0:
        x_coords, y_coords = zip(*requested_position)
        plt.scatter(x_coords, y_coords, color='green', s=0.5)
    plt.savefig(f'res/res_positions_{label}.png', dpi=300, bbox_inches='tight')

# Create an animation
def draw_animation(image_directory):
    image_files = [f"{image_directory}/{file}" for file in sorted(os.listdir(image_directory)) if file.lower().endswith((".png", ".jpg", ".jpeg"))]
    images = [Image.open(file) for file in image_files]
    gif_path = f"{image_directory}/animation.gif"
    images[0].save(gif_path, save_all=True, append_images=images[1:], loop=0, duration=200)  # Adjust duration as needed

