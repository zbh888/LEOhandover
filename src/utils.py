import random

import math
import matplotlib.pyplot as plt
from matplotlib.patches import Circle


class DataCollection:
    def __init__(self, graph_path):
        self.draw_path = graph_path
        self.x = []
        self.numberMessages = {}
        self.numberUEWaitingResponse = []

    def draw(self):
        # plot
        for id in self.numberMessages:
            plt.close('all')
            plt.clf()
            y = self.numberMessages[id]
            x = self.x
            plt.plot(x, y)
            plt.xlabel('Time (ms)')
            plt.ylabel('Number of Messages')
            plt.title('Satellite ' + str(id) + ' number of messages')
            plt.savefig(self.draw_path + '/sat_' + str(id) + 'numberMessages' + '.png')
        # plot
        plt.close('all')
        plt.clf()
        y = self.numberUEWaitingResponse
        x = self.x
        plt.plot(x, y)
        plt.xlabel('Time (ms)')
        plt.ylabel('Number of UE waiting for RRC configuration')
        plt.title('number of UEs waiting for response')
        plt.savefig(self.draw_path + '/numberUEwaitingforRRC.png')


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


def draw_from_positions(inactive_positions, active_position, requesting_position, label, dir, satellite_pos, R):
    plt.close('all')
    plt.clf()
    fig, ax = plt.subplots(figsize=(8, 8))
    x_range = (-1.2*R, 1.2*R)
    y_range = (-1.2*R, 1.2*R)
    plt.xlim(x_range)
    plt.ylim(y_range)
    if len(inactive_positions) != 0:
        x_coords, y_coords = zip(*inactive_positions)
        plt.scatter(x_coords, y_coords, color='red', s=0.5)
    if len(active_position) != 0:
        x_coords, y_coords = zip(*active_position)
        plt.scatter(x_coords, y_coords, color='blue', s=0.5)
    if len(requesting_position) != 0:
        x_coords, y_coords = zip(*requesting_position)
        plt.scatter(x_coords, y_coords, color='green', s=0.5)
    x_coords, y_coords = zip(*satellite_pos)
    plt.scatter(x_coords, y_coords, color='black', s=10)
    for point in satellite_pos:
        circle = Circle((point[0], point[1]), R, color='black', fill=False, linewidth=0.5)
        ax.add_patch(circle)
    plt.savefig(f'{dir}/res_positions_{label}.png', dpi=300, bbox_inches='tight')
