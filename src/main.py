import sys

import utils
from Satellite import *
from UE import *
from config import *
from AMF import *

dir = "defaultres"
if len(sys.argv) != 1:  # This is for automation
    dir = sys.argv[1]
    SATELLITE_CPU = int(sys.argv[2])
    SATELLITE_GROUND_DELAY = int(sys.argv[3])

file_path = f"res/{dir}"
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
file.close()

POSITIONS = utils.generate_points(NUMBER_UE, SATELLITE_R - 1 * 1000, 0, 0)


# POSITIONS = [(-13000, -20711), (-13000, -20711), (-13000, 20711)]
# POSITIONS = [(-13000, -20711)]

# ===================== Running Experiment =============================
# This is simply for tracing time stamp
def monitor_timestamp(env):
    while True:
        print(f"Current simulation time {env.now}", file=sys.stderr)
        yield env.timeout(1)


def stats_collector(env, UEs, satellites, timestep):
    while True:
        success_UE_positions = []
        request_UE_positions = []
        unrequested_UE_positions = []
        for ue_id in UEs:
            ue = UEs[ue_id]
            pos = (ue.position_x, ue.position_y)
            if ue.hasHandoverConfiguration:  # success
                success_UE_positions.append(pos)
            elif ue.sentHandoverRequest:
                request_UE_positions.append(pos)
            else:
                unrequested_UE_positions.append(pos)
        utils.draw_from_positions(unrequested_UE_positions, success_UE_positions, request_UE_positions, env.now,
                                  file_path + "/graph")
        yield env.timeout(timestep)


env = simpy.Environment()
# Deploy Core Function AMF

amf = AMF(core_delay=CORE_DELAY, env=env)

# Deploy source Satellite

satellite_source = Satellite(
    identity=1,
    position_x=0,
    position_y=0,
    velocity=SATELLITE_V,
    satellite_ground_delay=SATELLITE_GROUND_DELAY,
    ISL_delay=SATELLITE_SATELLITE_DELAY,
    core_delay=CORE_DELAY,
    AMF=amf,
    env=env)

UEs = {}
satellites = {}
satellites[1] = satellite_source
# Deploying UEs following randomly generated positions
for index, position in enumerate(POSITIONS, start=1):
    UEs[index] = UE(
        identity=index,
        position_x=position[0],
        position_y=position[1],
        serving_satellite=satellite_source,
        satellite_ground_delay=SATELLITE_GROUND_DELAY,
        env=env)

# Deploying other satellites
for i in range(2, NUMBER_SATELLITES + 1):
    satellites[i] = Satellite(
        identity=i,
        position_x=-15 * 1000,
        position_y=0,
        velocity=SATELLITE_V,
        satellite_ground_delay=SATELLITE_GROUND_DELAY,
        ISL_delay=SATELLITE_SATELLITE_DELAY,
        core_delay=CORE_DELAY,
        AMF=amf,
        env=env
    )

# Connecting objects

for identity in satellites:
    satellites[identity].UEs = UEs
    satellites[identity].satellites = satellites

for identity in UEs:
    UEs[identity].satellites = satellites

amf.satellites = satellites

env.process(monitor_timestamp(env))
env.process(stats_collector(env, UEs, satellites, 200))
print('==========================================')
print('============= Experiment Log =============')
print('==========================================')
env.run(until=DURATION)
print('==========================================')
print('============= Experiment Ends =============')
print('==========================================')

file = open(file_path + "/config_res.txt", "a")
counter_request = 0
counter_success = 0
for i in UEs:
    ue = UEs[i]
    if ue.hasHandoverConfiguration:
        counter_success += 1
    if ue.sentHandoverRequest:
        counter_request += 1
file.write(f"{counter_request} UEs sent the handover requests\n")
file.write(f"{counter_success} UEs received the handover configuration\n")
file.close()
