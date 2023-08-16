import simpy

from Base import *


class Satellite(Base):
    def __init__(self,
                 identity,
                 position_x,
                 position_y,
                 velocity,
                 satellite_ground_delay,
                 ISL_delay,
                 env):

        Base.__init__(self,
                      identity=identity,
                      position_x=position_x,
                      position_y=position_y,
                      env=env,
                      satellite_ground_delay=satellite_ground_delay,
                      object_type="satellite")

        # Config Initialization
        self.ISL_delay = ISL_delay
        self.velocity = velocity

        # Logic Initialization
        self.messageQ = simpy.Store(env)
        self.UEs = None
        self.satellites = None
        self.cpus = simpy.Resource(env, 8)  # Concurrent processing

        # Running process
        self.env.process(self.init())  # Print Deployment information
        self.env.process(self.update_position())
        self.env.process(self.handle_messages())

    def handle_messages(self):
        while True:
            msg = yield self.messageQ.get()
            print(f"{self.type} {self.identity} start handling msg:{msg} at time {self.env.now}")
            data = json.loads(msg)
            self.env.process(self.cpu_processing(data))

    # =================== Satellite functions ======================

    # The satellite receives the handover request from the UE

    # The logic will be handled here
    def cpu_processing(self, msg):
        with self.cpus.request() as request:
            # handle handover request from UE
            if msg['type'] == 'UE handover request':
                ueid = msg['from']
                UE = self.UEs[ueid]
                if self.connected(UE):
                    yield request
                    yield self.env.timeout(1)  # CPU process time
                if self.connected(UE):
                    # send the response to UE
                    data = {
                        "type": "target configuration request",
                        "ueid": ueid
                    }
                    # for now, just send it to the satellite 2. TODO
                    target_satellite = self.satellites[2]
                    self.env.process(
                        self.send_message(
                            delay=self.ISL_delay,
                            msg=data,
                            Q=target_satellite.messageQ,
                            to=target_satellite
                        )
                    )
            elif msg['type'] == 'target configuration response':
                satellite_id = msg['from']
                ueid = msg['ueid']
                UE = self.UEs[ueid]
                if self.connected(UE):
                    yield request
                    yield self.env.timeout(1)  # CPU process time
                if self.connected(UE):
                    # send the response to UE
                    data = {
                        "type": "handover request response",
                    }
                    self.env.process(
                        self.send_message(
                            delay=self.satellite_ground_delay,
                            msg=data,
                            Q=UE.messageQ,
                            to=UE
                        )
                    )
            elif msg['type'] == 'target configuration request':
                satellite_id = msg['from']
                ueid = msg['ueid']
                yield request
                yield self.env.timeout(1)  # CPU process time
                # send the response to UE
                data = {
                    "type": "target configuration response",
                    "ueid": ueid
                }
                source_satellite = self.satellites[satellite_id]
                self.env.process(
                    self.send_message(
                        delay=self.ISL_delay,
                        msg=data,
                        Q=source_satellite.messageQ,
                        to=source_satellite
                    )
                )

    def update_position(self):
        while True:
            yield self.env.timeout(1)  # Time between position updates
            # Update x and y based on velocity
            # Calculate time ratio
            ratio = 1 / 1000
            # direction set to right
            self.position_x += self.velocity * ratio

    # ==================== Utils (Not related to Simpy) ==============
    def connected(self, UE):
        return (UE.active and UE.serving_satellite.identity == self.identity)
