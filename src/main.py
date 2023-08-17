import sys

import utils
from Satellite import *
from UE import *
from config import *

print("System Configuration:")
print(f"  #Satellite Radius: {SATELLITE_R} m")
print(f"  #Satellite speed: {SATELLITE_V} m/s")
print(f"  #Number of UEs: {NUMBER_UE}")
print(f"  #Satellite to ground delay: {SATELLITE_GROUND_DELAY} ms")
print(f"  #Inter Satellite delay: {SATELLITE_SATELLITE_DELAY} ms")

t = 1
d = SATELLITE_V * t
number_handover = utils.handout(SATELLITE_R, NUMBER_UE, d)
print(f"  #Example: approximate {number_handover} need to be handed over within {t} seconds")

POSITIONS = utils.generate_points(NUMBER_UE, SATELLITE_R - 1 * 1000, 0, 0)
print('Randomly generating UE positions Success')

POSITIONS = [(-13000, -20711), (-13000, -20711), (-13000, 20711)]
POSITIONS = [(-13000, -20711)]

# ===================== Running Experiment =============================
# This is simply for tracing time stamp
def monitor_timestamp(env):
    while True:
        print(f"Current simulation time {env.now}", file=sys.stderr)
        yield env.timeout(1)


env = simpy.Environment()
# Deploy source Satellite

satellite_source = Satellite(
    identity=1,
    position_x=0,
    position_y=0,
    velocity=SATELLITE_V,
    satellite_ground_delay=SATELLITE_GROUND_DELAY,
    ISL_delay=SATELLITE_SATELLITE_DELAY,
    env=env)

UEs = {}
satellites = {1: satellite_source}

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
        position_x=0,
        position_y=0,
        velocity=SATELLITE_V,
        satellite_ground_delay=SATELLITE_GROUND_DELAY,
        ISL_delay=SATELLITE_SATELLITE_DELAY,
        env=env
    )

for identity in satellites:
    satellites[identity].UEs = UEs
    satellites[identity].satellites = satellites

# env.process(monitor_timestamp(env))
print('==========================================')
print('============= Experiment Log =============')
print('==========================================')
env.run(until=500)

print('==========================================')
print('============= Experiment Ends =============')
print('==========================================')
counter_request = 0
counter_success = 0
Success_UE_Positions = []
for i in UEs:
    ue = UEs[i]
    if ue.hasNoHandoverRequest == False:
        counter_request += 1
    if ue.hasNoHandoverConfiguration == False:
        counter_success += 1
        Success_UE_Positions.append((ue.position_x, ue.position_y))
print(f"{counter_request} UEs sent the handover requests")
print(f"{counter_success} UEs received the handover configuration")
utils.draw_from_positions(POSITIONS, Success_UE_Positions)
