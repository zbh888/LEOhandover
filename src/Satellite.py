import json

import simpy


class Satellite(object):
    def __init__(self,
                 identity,
                 position_x,
                 position_y,
                 velocity,
                 satellite_ground_delay,
                 target_satellite,
                 ISL_delay,
                 env):

        # Config Initialization
        self.ISL_delay = ISL_delay
        self.target_satellite = target_satellite
        self.satellite_ground_delay = satellite_ground_delay
        self.identity = identity
        self.env = env
        self.position_x = position_x
        self.position_y = position_y
        self.velocity = velocity

        # Logic Initialization
        self.handover_request_Q = simpy.Store(env)
        self.configuration_response_Q = simpy.Store(env)
        self.UEs = {}
        self.cpus = simpy.Resource(env, 8)  # Concurrent processing

        # Running process
        self.env.process(self.init())  # Print Deployment information
        self.env.process(self.update_position())
        self.env.process(self.process_handover_request())

    def init(self):
        print(f"Satellite {self.identity} deployed at time {self.env.now}")
        yield self.env.timeout(1)

    def send_message(self, delay, msg, Q, target):
        print(f"Satellite {self.identity} sends {target.identity}: message {msg} at {self.env.now}")
        yield self.env.timeout(delay)
        Q.put(msg)

    # The satellite receives the handover request from the UE
    def process_handover_request(self):
        while True:
            msg = yield self.handover_request_Q.get()
            print(f"Satellite {self.identity} receives msg:{msg} at time {self.env.now}")
            sender = json.loads(msg)['ueid']
            self.env.process(self.cpu_processing(sender))

    def process_configuration_response(self):
        while True:
            msg = yield self.handover_request_Q.get()
            print(f"Satellite {self.identity} receives msg:{msg} at time {self.env.now}")
            sender = json.loads(msg)['ueid']
            self.env.process(self.cpu_processing(sender))

    def cpu_processing(self, ueid):
        with self.cpus.request() as request:
            UE = self.UEs[ueid]
            if UE.active:
                yield request
                yield self.env.timeout(1)
            if UE.active:
                # return the response to UE
                data = {
                    "type": "handover request response",
                    "satid": self.identity,
                    "ueid": UE.identity}
                msg = json.dumps(data)
                self.env.process(self.send_message(self.satellite_ground_delay, msg, UE.responseQ, UE))
            #   print(f"Satellite {self.identity} sends response {res} at time {env.now}")

    def update_position(self):
        while True:
            yield self.env.timeout(1)  # Time between position updates
            # Update x and y based on velocity
            # Calculate time ratio
            ratio = 1 / 1000
            # direction set to right
            self.position_x += self.velocity * ratio

        # For convenience, the target satellite is first separated.


class targetSatellite(object):
    def __init__(self, identity, x, y, v, ISL_delay, env):
        self.ISL_delay = ISL_delay
        self.identity = identity
        self.env = env
        self.x = x
        self.y = y
        self.v = v
        # This Q is for computing the response to source satellite
        self.configure_request_Q = simpy.Store(env)

        self.cpus = simpy.Resource(env, 8)  # Concurrent processing

        self.env.process(self.init())

    # self.env.process(self.process_handover_request())

    def init(self):
        print(f"Satellite {self.identity} deployed at time {self.env.now}")
        yield self.env.timeout(1)

    def process_configuration_request(self):
        while True:
            msg = yield self.configureQ.get()
            print(f"Satellite {self.identity} receives msg:{msg} at time {self.env.now}")
            # sender = msg[]
            self.env.process(self.cpu_processing())
