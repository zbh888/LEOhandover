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


# ===================== Running Experiment =============================
# This is simply for tracing time stamp
def monitor_timestamp(env):
    while True:
        print(f"Current simulation time {env.now}", file=sys.stderr)
        yield env.timeout(1)


env = simpy.Environment()
# Deploy Satellites
satellite2 = targetSatellite(2, 0, 0, SATELLITE_V, SATELLITE_SATELLITE_DELAY, env)

satellite1 = Satellite(
    identity=1,
    position_x=0,
    position_y=0,
    velocity=SATELLITE_V,
    satellite_ground_delay=SATELLITE_GROUND_DELAY,
    target_satellite=satellite2,
    ISL_delay=SATELLITE_SATELLITE_DELAY,
    env=env)

# Deploying UEs following randomly generated positions
for index, position in enumerate(POSITIONS, start=1):
    satellite1.UEs[index] = UE(
        identity=index,
        position_x=position[0],
        position_y=position[1],
        serving_satellite=satellite1,
        satellite_ground_delay=SATELLITE_GROUND_DELAY,
        env=env)

# env.process(monitor_timestamp(env))
print('==========================================')
print('============= Experiment Log =============')
print('==========================================')
env.run(until=10)
