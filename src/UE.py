import json

import math
import simpy


class UE:
    def __init__(self,
                 identity,
                 position_x,
                 position_y,
                 serving_satellite,
                 satellite_ground_delay,
                 env):

        # Config Initialization
        self.type = "UE"
        self.identity = identity
        self.position_x = position_x
        self.position_y = position_y
        self.env = env
        self.serving_satellite = serving_satellite
        self.satellite_ground_delay = satellite_ground_delay

        # Logic Initialization
        self.messageQ = simpy.Store(env)
        self.active = True
        self.hasNoHandoverConfiguration = True
        self.hasNoHandoverRequest = True

        # Running Process
        env.process(self.init())
        env.process(self.handover_request_monitor())
        env.process(self.service_monitor())
        env.process(self.response_monitor())

    def init(self):
        print(
            f"UE {self.identity} deployed at time {self.env.now}, positioned at ({self.position_x},{self.position_y})")
        yield self.env.timeout(1)

    def send_message(self, delay, msg, Q, to):
        msg['from'] = self.identity
        msg['to'] = to.identity
        msg = json.dumps(msg)
        print(f"UE {self.identity} sends {to.type} {to.identity} the message {msg} at {self.env.now}")
        yield self.env.timeout(delay)
        Q.put(msg)

    # =================== UE functions ======================
    def handover_request_monitor(self):
        while self.active:
            if self.send_request_condition():
                data = {
                    "type": "UE handover request",
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

    def response_monitor(self):
        msg = yield self.messageQ.get()
        # yield self.env.timeout(self.delay)
        satid = json.loads(msg)['from']
        if satid == self.serving_satellite.identity and self.active:
            self.hasNoHandoverConfiguration = False
            print(f"UE {self.identity} receives the configuration at {self.env.now}")

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
