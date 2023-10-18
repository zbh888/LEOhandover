import simpy

from Base import *
from config import *


class AMF(Base):
    def __init__(self,
                 core_delay,
                 env):

        Base.__init__(self,
                      identity=1,
                      position_x=0,
                      position_y=0,
                      env=env,
                      satellite_ground_delay=0,
                      object_type="AMF")

        # Config Initialization
        self.core_delay = core_delay
        self.satellites = None

        # Logic Initialization
        self.messageQ = simpy.Store(env)
        self.cpus = simpy.Resource(env, 100)  # Concurrent processing

        # Running process
        self.env.process(self.init())  # Print Deployment information
        self.env.process(self.handle_messages())

    def handle_messages(self):
        """ Get the task from message Q and start a CPU processing process """
        while True:
            msg = yield self.messageQ.get()
            print(f"{self.type} {self.identity} start handling msg:{msg} at time {self.env.now}")
            data = json.loads(msg)
            self.env.process(self.cpu_processing(data))

    # =================== Satellite functions ======================

    def cpu_processing(self, msg):
        """ Processing the task from the message Q

        Args:
            msg: the json object from message Q

        """
        with self.cpus.request() as request:
            # Get the task and processing time
            task = msg['task']
            processing_time = PROCESSING_TIME[task]

            # handle the task by cases
            if task == PATH_SHIFT_REQUEST:
                satellite_id = msg['from']
                previous_id = msg['previous_id']
                satellite = self.satellites[satellite_id]
                previous_satellite = self.satellites[previous_id]
                yield request
                yield self.env.timeout(processing_time)
                data1 = {
                    "task": AMF_RESPONSE,
                }
                self.env.process(
                    self.send_message(
                        delay=self.core_delay,
                        msg=data1,
                        Q=satellite.messageQ,
                        to=satellite
                    )
                )
                data2 = {
                    "task": AMF_RESPONSE,
                }
                self.env.process(
                    self.send_message(
                        delay=self.core_delay,
                        msg=data2,
                        Q=previous_satellite.messageQ,
                        to=previous_satellite
                    )
                )

