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
        self.satellites = None
        self.active = True
        self.hasNoHandoverConfiguration = True
        self.hasNoHandoverRequest = True

        # Running Process
        env.process(self.init())
        env.process(self.handle_messages())

        env.process(self.handover_request_monitor())
        env.process(self.service_monitor())

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
                    self.hasNoHandoverConfiguration = False
                    print(f"{self.type} {self.identity} receives the configuration at {self.env.now}")

    def handover_request_monitor(self):
        while self.active:
            if self.send_request_condition():
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
                self.hasNoHandoverRequest = False
            else:
                yield self.env.timeout(1)

    def service_monitor(self):
        while True:
            if self.outside_coverage():
                print(
                    f"UE {self.identity} lost connection at time {self.env.now} from satellite {self.serving_satellite.identity}")
                self.active = False
                break
            else:
                yield self.env.timeout(1)  # Wait for 1 time unit before testing again

    # ==================== Utils (Not related to Simpy) ==============
    def send_request_condition(self):
        d = math.sqrt(((self.position_x - self.serving_satellite.position_x) ** 2) + (
                (self.position_y - self.serving_satellite.position_y) ** 2))
        decision = (d > 23 * 1000 and self.position_x < self.serving_satellite.position_x
                    and self.hasNoHandoverConfiguration and self.hasNoHandoverRequest)
        return decision

    def outside_coverage(self):
        d = math.sqrt(((self.position_x - self.serving_satellite.position_x) ** 2) + (
                (self.position_y - self.serving_satellite.position_y) ** 2))
        return d >= 25 * 1000
