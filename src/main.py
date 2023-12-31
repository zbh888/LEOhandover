import sys
import  os
import utils
from AMF import *
from Satellite import *
from UE import *
import math
import random

random.seed(SEED)

dir = "defaultres"
if len(sys.argv) != 1:  # This is for automation
    dir = sys.argv[1]
    SATELLITE_CPU = int(sys.argv[2])
    SATELLITE_GROUND_DELAY = int(sys.argv[3])

file_path = f"res/{dir}"
for id in POS_SATELLITES:
    os.mkdir(file_path + "/graph_data/sat_" + str(id))

file = open(file_path + "/config_res.txt", "w")
# Close the file
file.write("System Configuration:\n")
file.write(f"  #Satellite Radius: {SATELLITE_R} m\n")
file.write(f"  #Satellite speed: {SATELLITE_V} m/s\n")
file.write(f"  #Number of UEs: {NUMBER_UE}\n")
file.write(f"  #Satellite CPU number: {SATELLITE_CPU}\n")
file.write(f"  #Satellite to ground delay: {SATELLITE_GROUND_DELAY} ms\n")
file.write(f"  #Inter Satellite delay: {SATELLITE_SATELLITE_DELAY} ms\n")

t = 1
d = SATELLITE_V * t
number_handover = utils.handout(SATELLITE_R, NUMBER_UE, d)
file.write(f"  #Example: approximate {number_handover} need to be handed over within {t} seconds\n")
t = 0.001
d = SATELLITE_V * t
number_handover = utils.handout(SATELLITE_R, NUMBER_UE, d)
file.write(f"  #Example: approximate {number_handover} need to be handed over within {t} seconds\n")
file.close()

# We use this if the satellites is not linearly deployed
 #POSITIONS = utils.generate_points(NUMBER_UE, SATELLITE_R - 1 * 1000, 0, 0)

 # We use this if the satellites are linearly deployed
if len(POS_SATELLITES) < 4:
    ylim_intersect = math.sqrt(SATELLITE_R ** 2 - (HORIZONTAL_DISTANCE / 2) ** 2) - 500
    ylim = (ylim_intersect // GROUP_AREA_L - 1) * GROUP_AREA_L
else:
    ylim_half = VERTICAL_DISTANCE / 2 - 200
    ylim = (ylim_half // GROUP_AREA_L - 1) * GROUP_AREA_L
POSITIONS = utils.generate_points_with_ylim(NUMBER_UE, SATELLITE_R - 100, 0, 0, ylim)
# ===================== Running Experiment =============================
# This is simply for tracing time stamp
def monitor_timestamp(env):
    while True:
        print(f"Current simulation time {env.now}", file=sys.stderr)
        yield env.timeout(1)


'''
The function draws screenshot of global Status. 
As drawing takes time, the timestep has to be big.
'''


def global_stats_collector_draw_middle(env, UEs, satellites, timestep):
    while True:
        active_UE_positions = []
        requesting_UE_positions = []
        inactive_positions = []
        for ue_id in UEs:
            ue = UEs[ue_id]
            pos = (ue.position_x, ue.position_y)
            if ue.state == ACTIVE:  # success
                active_UE_positions.append(pos)
            elif ue.state == INACTIVE:
                inactive_positions.append(pos)
            else:
                requesting_UE_positions.append(pos)
        satellite_positions = []
        for s_id in satellites:
            s = satellites[s_id]
            satellite_positions.append((s.position_x, s.position_y))
        utils.draw_from_positions(inactive_positions, active_UE_positions, requesting_UE_positions, env.now,
                                  file_path + "/graph", satellite_positions, SATELLITE_R)
        yield env.timeout(timestep)


'''
This function collects information but draws in the end of the simulation.
'''


def global_stats_collector_draw_final(env, data, UEs, satellites, timestep):
    while True:
        data.x.append(env.now)
        for id in satellites:
            satellite = satellites[id]
            counter = satellite.counter
            if id not in data.numberUnProcessedMessages:
                data.numberUnProcessedMessages[id] = []
                data.cumulative_total_messages[id] = []
                data.cumulative_message_from_UE_measurement[id] = []
                data.cumulative_message_from_UE_retransmit[id] = []
                data.cumulative_message_from_UE_RA[id] = []
                data.cumulative_message_from_satellite[id] = []
                data.cumulative_message_from_dropped[id] = []
                data.cumulative_message_from_AMF[id] = []

            data.numberUnProcessedMessages[id].append(len(satellite.cpus.queue))
            data.cumulative_total_messages[id].append(counter.total_messages)
            data.cumulative_message_from_UE_measurement[id].append(counter.message_from_UE_measurement)
            data.cumulative_message_from_UE_retransmit[id].append(counter.message_from_UE_retransmit)
            data.cumulative_message_from_UE_RA[id].append(counter.message_from_UE_RA)
            data.cumulative_message_from_satellite[id].append(counter.message_from_satellite)
            data.cumulative_message_from_dropped[id].append(counter.message_dropped)
            data.cumulative_message_from_AMF[id].append(counter.message_from_AMF)
        numberUEWaitingRRC = 0
        for id in UEs:
            UE = UEs[id]
            if UE.state == WAITING_RRC_CONFIGURATION:
                numberUEWaitingRRC += 1
        data.numberUEWaitingResponse.append(numberUEWaitingRRC)
        yield env.timeout(timestep)


env = simpy.Environment()
# Deploy Core Function AMF

amf = AMF(core_delay=CORE_DELAY, env=env)

# Deploy source Satellite
UEs = {}
satellites = {}

for sat_id in POS_SATELLITES:
    pos = POS_SATELLITES[sat_id]
    satellites[sat_id] = Satellite(
        identity=sat_id,
        position_x=pos[0],
        position_y=pos[1],
        velocity=SATELLITE_V,
        satellite_ground_delay=SATELLITE_GROUND_DELAY,
        ISL_delay=SATELLITE_SATELLITE_DELAY,
        core_delay=CORE_DELAY,
        AMF=amf,
        env=env)

# Deploying UEs following randomly generated positions
for index, position in enumerate(POSITIONS, start=1):
    UEs[index] = UE(
        identity=index,
        position_x=position[0],
        position_y=position[1],
        serving_satellite=satellites[1],
        satellite_ground_delay=SATELLITE_GROUND_DELAY,
        env=env)

# Connecting objects

for identity in satellites:
    satellites[identity].UEs = UEs
    satellites[identity].satellites = satellites

for identity in UEs:
    UEs[identity].satellites = satellites

amf.satellites = satellites

env.process(monitor_timestamp(env))
env.process(global_stats_collector_draw_middle(env, UEs, satellites, 200))
data = utils.DataCollection(file_path + "/graph_data")
env.process(global_stats_collector_draw_final(env, data, UEs, satellites, 1))
print('==========================================')
print('============= Experiment Log =============')
print('==========================================')
env.run(until=DURATION)
print('==========================================')
print('============= Experiment Ends =============')
print('==========================================')

data.read_UEs(UEs)
# draw from data
data.draw()
