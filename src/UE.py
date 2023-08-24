import math
import simpy

from Base import *
from config import *


class UE(Base):
    def __init__(self,
                 identity,
                 position_x,
                 position_y,
                 satellite_ground_delay,
                 serving_satellite,
                 env):

        # Config Initialization
        Base.__init__(self,
                      identity=identity,
                      position_x=position_x,
                      position_y=position_y,
                      env=env,
                      satellite_ground_delay=satellite_ground_delay,
                      object_type="UE")

        self.serving_satellite = serving_satellite

        # Logic Initialization
        self.messageQ = simpy.Store(env)
        self.cpus = simpy.Resource(env, UE_CPU)
        self.state = ACTIVE
        self.satellites = None

        self.active = True
        self.hasHandoverConfiguration = False
        self.sentHandoverRequest = False
        self.sentRrcReconfigurationComplete = False
        self.handoverComplete = False

        self.lock = False  # I only want this to perform one handover
        self.targetID = None

        # Running Process
        env.process(self.init())
        env.process(self.handle_messages())

        env.process(self.action_monitor())

    # =================== UE functions ======================
    def handle_messages(self):
        while True:
            msg = yield self.messageQ.get()
            print(f"{self.type} {self.identity} start handling msg:{msg} at time {self.env.now}")
            data = json.loads(msg)
            self.env.process(self.cpu_processing(data))

    def cpu_processing(self, msg):
        with self.cpus.request() as request:
            task = msg['task']
            if task == RRC_RECONFIGURATION:
                yield request
                satid = msg['from']
                if satid == self.serving_satellite.identity and self.active:
                    # get candidate target
                    targets = msg['targets']
                    # choose target
                    self.targetID = targets[0]
                    self.hasHandoverConfiguration = True
                    print(f"{self.type} {self.identity} receives the configuration at {self.env.now}")
            elif task == RRC_RECONFIGURATION_COMPLETE_RESPONSE:
                yield request
                satid = msg['from']
                satellite = self.satellites[satid]
                if self.covered_by(satid):
                    self.serving_satellite = satellite
                    self.handoverComplete = True
                    print(f"{self.type} {self.identity} finished handover at {env.now}")

    def action_monitor(self):
        while True:
            # send measurement report
            if self.send_request_condition() and self.active and not self.lock:
                data = {
                    "task": MEASUREMENT_REPORT,
                }
                self.env.process(
                    self.send_message(
                        delay=self.satellite_ground_delay,
                        msg=data,
                        Q=self.serving_satellite.messageQ,
                        to=self.serving_satellite
                    )
                )
                self.sentHandoverRequest = True
                self.lock = True
            if self.hasHandoverConfiguration:  # When the UE has the configuration
                if self.targetID and self.covered_by(self.targetID) and not self.sentRrcReconfigurationComplete:
                    target = self.satellites[self.targetID]
                    data = {
                        "task": RRC_RECONFIGURATION_COMPLETE,
                    }
                    self.env.process(
                        self.send_message(
                            delay=self.satellite_ground_delay,
                            msg=data,
                            Q=target.messageQ,
                            to=target
                        )
                    )
                    self.sentRrcReconfigurationComplete = True
            # switch to inactive
            if self.outside_coverage() and self.active:
                print(
                    f"UE {self.identity} lost connection at time {self.env.now} from satellite {self.serving_satellite.identity}")
                self.active = False
            yield self.env.timeout(1)

    # ==================== Utils (Not related to Simpy) ==============
    def covered_by(self, satelliteID):
        satellite = self.satellites[satelliteID]
        d = math.sqrt(((self.position_x - satellite.position_x) ** 2) + (
                (self.position_y - satellite.position_y) ** 2))
        return d <= 25 * 1000

    def send_request_condition(self):
        d = math.sqrt(((self.position_x - self.serving_satellite.position_x) ** 2) + (
                (self.position_y - self.serving_satellite.position_y) ** 2))
        decision = (d > 23 * 1000 and self.position_x < self.serving_satellite.position_x
                    and not self.hasHandoverConfiguration and not self.sentHandoverRequest)
        return decision

    def outside_coverage(self):
        d = math.sqrt(((self.position_x - self.serving_satellite.position_x) ** 2) + (
                (self.position_y - self.serving_satellite.position_y) ** 2))
        # TODO this is not accurate
        return d >= 25 * 1000 and self.position_x < self.serving_satellite.position_x
