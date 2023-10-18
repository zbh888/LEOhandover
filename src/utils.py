import math
import pickle
import random

import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import hashlib

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

def generate_points_with_ylim(n, R, x, y, ylim):
    def generate_one(R, x, y):
        r = R * math.sqrt(random.uniform(0, 1))
        theta = random.uniform(0, 1) * 2 * math.pi
        px = x + r * math.cos(theta)
        py = y + r * math.sin(theta)
        return px, py

    points = []
    while len(points) < n:
        x_, y_ = generate_one(R, x, y)
        if abs(y_) < ylim:
            points.append((x_, y_))
    return points

# ===================== Data Collection and drawing =============================

class DataCollection:
    def __init__(self, graph_path):
        self.draw_path = graph_path
        self.x = []
        self.numberUnProcessedMessages = {}
        self.numberUEWaitingResponse = []

        self.cumulative_total_messages = {}
        self.cumulative_message_from_UE_measurement = {}
        self.cumulative_message_from_UE_retransmit = {}
        self.cumulative_message_from_UE_RA = {}
        self.cumulative_message_from_satellite = {}
        self.cumulative_message_from_UE_Group = {}
        # new things
        self.cumulative_message_from_UE_Group_retransmit = {}
        self.cumulative_message_from_dropped_from_non_group = {}
        self.cumulative_message_from_dropped_from_group = {}

        self.UE_time_stamp = {}
        self.UE_positions = {}
        self.UE_groupID = {}

    def read_UEs(self, UEs):
        for id in UEs:
            UE = UEs[id]
            self.UE_time_stamp[id] = UE.timestamps
            self.UE_positions[id] = (UE.position_x, UE.position_y)
            self.UE_groupID[id] = UE.groupID

    def draw(self):
        # plot
        for id in self.numberUnProcessedMessages:
            plt.close('all')
            plt.clf()
            y = self.numberUnProcessedMessages[id]
            x = self.x
            plt.plot(x, y)
            plt.xlabel('Time (ms)')
            plt.ylabel('Number of Messages')
            plt.title('Satellite ' + str(id) + ' number of unprocessed total messages')
            plt.savefig(self.draw_path + '/sat_' + str(id) + '/' + str(id) + 'numberUnProcessedMessages' + '.png')

        for id in self.cumulative_message_from_UE_Group:
            plt.close('all')
            plt.clf()
            y = self.cumulative_message_from_UE_Group[id]
            x = self.x
            plt.plot(x, y)
            plt.xlabel('Time (ms)')
            plt.ylabel('Number of Messages')
            plt.title('Satellite ' + str(id) + ' number of cumulative group messages')
            plt.savefig(self.draw_path + '/sat_' + str(id) + '/' + str(id) + 'cumulative_group_messages' + '.png')

        for id in self.cumulative_total_messages:
            plt.close('all')
            plt.clf()
            y = self.cumulative_total_messages[id]
            x = self.x
            plt.plot(x, y)
            plt.xlabel('Time (ms)')
            plt.ylabel('Number of Messages')
            plt.title('Satellite ' + str(id) + ' number of cumulative total messages')
            plt.savefig(self.draw_path + '/sat_' + str(id) + '/' + str(id) + 'cumulative_total_messages' + '.png')

        for id in self.cumulative_message_from_UE_measurement:
            plt.close('all')
            plt.clf()
            y = self.cumulative_message_from_UE_measurement[id]
            x = self.x
            plt.plot(x, y)
            plt.xlabel('Time (ms)')
            plt.ylabel('Number of Messages')
            plt.title('Satellite ' + str(id) + ' number of cumulative UE request messages')
            plt.savefig(self.draw_path + '/sat_' + str(id) + '/' + str(id) + 'cumulative_message_from_UE_measurement' + '.png')

        for id in self.cumulative_message_from_UE_retransmit:
            plt.close('all')
            plt.clf()
            y = self.cumulative_message_from_UE_retransmit[id]
            x = self.x
            plt.plot(x, y)
            plt.xlabel('Time (ms)')
            plt.ylabel('Number of Messages')
            plt.title('Satellite ' + str(id) + ' number of UE cumulative retransmit messages')
            plt.savefig(self.draw_path + '/sat_' + str(id) + '/' + str(id) + 'cumulative_message_from_UE_retransmit' + '.png')

        for id in self.cumulative_message_from_UE_RA:
            plt.close('all')
            plt.clf()
            y = self.cumulative_message_from_UE_RA[id]
            x = self.x
            plt.plot(x, y)
            plt.xlabel('Time (ms)')
            plt.ylabel('Number of Messages')
            plt.title('Satellite ' + str(id) + ' number of cumulative UE RA messages')
            plt.savefig(self.draw_path + '/sat_' + str(id) + '/' + str(id) + 'cumulative_message_from_UE_RA' + '.png')

        for id in self.cumulative_message_from_satellite:
            plt.close('all')
            plt.clf()
            y = self.cumulative_message_from_satellite[id]
            x = self.x
            plt.plot(x, y)
            plt.xlabel('Time (ms)')
            plt.ylabel('Number of Messages')
            plt.title('Satellite ' + str(id) + ' number of cumulative satellite messages')
            plt.savefig(self.draw_path + '/sat_' + str(id) + '/' + str(id) + 'cumulative_message_from_satellite' + '.png')

        for id in self.cumulative_message_from_UE_Group_retransmit:
            plt.close('all')
            plt.clf()
            y = self.cumulative_message_from_UE_Group_retransmit[id]
            x = self.x
            plt.plot(x, y)
            plt.xlabel('Time (ms)')
            plt.ylabel('Number of Messages')
            plt.title('Satellite ' + str(id) + ' number of cumulative group retransmission')
            plt.savefig(self.draw_path + '/sat_' + str(id) + '/' + str(id) + 'cumulative_message_from_UE_Group_retransmit' + '.png')
        for id in self.cumulative_message_from_dropped_from_group:
            plt.close('all')
            plt.clf()
            y = self.cumulative_message_from_dropped_from_group[id]
            x = self.x
            plt.plot(x, y)
            plt.xlabel('Time (ms)')
            plt.ylabel('Number of Messages')
            plt.title('Satellite ' + str(id) + ' number of dropped group request')
            plt.savefig(self.draw_path + '/sat_' + str(id) + '/' + str(id) + 'cumulative_message_from_dropped_from_group' + '.png')
        for id in self.cumulative_message_from_dropped_from_non_group:
            plt.close('all')
            plt.clf()
            y = self.cumulative_message_from_dropped_from_non_group[id]
            x = self.x
            plt.plot(x, y)
            plt.xlabel('Time (ms)')
            plt.ylabel('Number of Messages')
            plt.title('Satellite ' + str(id) + ' number of dropped non-group request')
            plt.savefig(self.draw_path + '/sat_' + str(id) + '/' + str(id) + 'cumulative_message_from_dropped_from_non_group' + '.png')


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

        with open(self.draw_path + 'data_object.pkl', 'wb') as outp:
            pickle.dump(self, outp, pickle.HIGHEST_PROTOCOL)


def draw_from_positions(inactive_positions, active_position, requesting_position, group_requesting_position, label, dir, satellite_pos, R):
    plt.close('all')
    plt.clf()
    fig, ax = plt.subplots(figsize=(8, 8))
    x_range = (-1.2 * R, 1.2 * R)
    y_range = (-1.2 * R, 1.2 * R)
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
    if len(group_requesting_position) != 0:
        x_coords, y_coords = zip(*group_requesting_position)
        plt.scatter(x_coords, y_coords, color='yellow', s=0.5)
    x_coords, y_coords = zip(*satellite_pos)
    plt.scatter(x_coords, y_coords, color='black', s=10)
    for point in satellite_pos:
        circle = Circle((point[0], point[1]), R, color='black', fill=False, linewidth=0.5)
        ax.add_patch(circle)
    plt.savefig(f'{dir}/res_positions_{label}.png', dpi=300, bbox_inches='tight')

# ===================== clustering =============================

def determine_group_threshold(UEs, group_area_length):
    c1, c2, c3, c4 = 0, 0, 0, 0
    for id in UEs:
        UE = UEs[id]
        res = determine_groupID(UE.position_x, UE.position_y, group_area_length)
        if res == (1, 1):
            c1 += 1
        if res == (-1, -1):
            c2 += 1
        if res == (1, -1):
            c3 += 1
        if res == (-1, 1):
            c4 += 1
    return (c1 + c2 + c3 + c4) / 4


def determine_groupID(x, y, area_length):
    if x >= 0:
        res_x = (x // area_length) + 1
    else:
        res_x = (x // area_length)
    if y >= 0:
        res_y = (y // area_length) + 1
    else:
        res_y = (y // area_length)
    return int(res_x), int(res_y)


def assign_group(UEs, area_length):
    for id in UEs:
        UE = UEs[id]
        x, y = determine_groupID(UE.position_x, UE.position_y, area_length)
        groupID = str(x) + "_" + str(y)
        UEs[id].groupID = groupID

def determine_edge_point(x,y,area_length):
    if x < 0:
        left = x
        right = (x + 1)
    else:
        left = (x - 1)
        right = x

    if y < 0:
        up = y + 1
        down = y
    else:
        up = y
        down = y - 1

    left *= area_length
    right *= area_length
    up *= area_length
    down *= area_length

    # left up
    ul = (left, up)
    # right up
    ru = (right, up)
    # right down
    rd = (right, down)
    # left down
    ld = (left, down)
    return ul, ru, rd, ld


# ===================== Secret Sharing =============================
def generate_share():
    return random.randint(10000000, 100000000)

def generate_commitment(share):
    result = str(share)
    #encode_int = str(share).encode()
    #result = hashlib.md5(encode_int).hexdigest()
    return result

def verify_share_commitment(share, commitment):
    return generate_commitment(share) == commitment
