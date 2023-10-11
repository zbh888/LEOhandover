import random

import simpy
import math
from Base import *
from config import *
import utils

class cumulativeMessageCount:
    def __init__(self):
        self.total_messages = 0
        self.message_from_UE_measurement = 0
        self.message_from_UE_retransmit = 0
        self.message_from_UE_RA = 0
        self.message_from_satellite = 0

    def increment_UE_measurement(self):
        self.total_messages += 1
        self.message_from_UE_measurement += 1

    def increment_UE_retransmit(self):
        self.total_messages += 1
        self.message_from_UE_retransmit += 1

    def increment_satellite(self):
        self.total_messages += 1
        self.message_from_satellite += 1

    def increment_UE_RA(self):
        self.total_messages += 1
        self.message_from_UE_RA += 1


class Satellite(Base):
    def __init__(self,
                 identity,
                 position_x,
                 position_y,
                 velocity,
                 satellite_ground_delay,
                 ISL_delay,
                 core_delay,
                 AMF,
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
        self.core_delay = core_delay

        # Logic Initialization
        self.messageQ = simpy.Store(env)
        self.AMF = AMF
        self.UEs = None
        self.satellites = None
        self.cpus = simpy.PriorityResource(env, capacity=SATELLITE_CPU)  # Concurrent processing
        self.counter = cumulativeMessageCount()
        self.group_count = {}
        self.group_aggregators = {}
        self.hybrid_threshold = None

        # Running process
        self.env.process(self.init())  # Print Deployment information
        self.env.process(self.update_position())
        self.env.process(self.monitor_group_information())
        self.env.process(self.handle_messages())

    def handle_messages(self):
        """ Get the task from message Q and start a CPU processing process """
        while True:
            msg = yield self.messageQ.get()
            data = json.loads(msg)
            task = data['task']
            if task == MEASUREMENT_REPORT or task == RETRANSMISSION:
                if len(self.cpus.queue) < QUEUED_SIZE:
                    print(f"{self.type} {self.identity} accepted msg:{msg} at time {self.env.now}")
                    self.env.process(self.cpu_processing(msg=data, priority=2))
                else:
                    print(f"{self.type} {self.identity} dropped msg:{msg} at time {self.env.now}")
            else:
                print(f"{self.type} {self.identity} accepted msg:{msg} at time {self.env.now}")
                self.env.process(self.cpu_processing(msg=data, priority=1))

    # =================== Satellite functions ======================

    def cpu_processing(self, msg, priority):
        """ Processing the task from the message Q

        Args:
            msg: the json object from message Q

        """
        with self.cpus.request(priority=priority) as request:
            yield request
            print(f"{self.type} {self.identity} handling msg:{msg} at time {self.env.now}")
            # Get the task and processing time
            task = msg['task']

            # handle the task by cases
            if task == MEASUREMENT_REPORT or task == RETRANSMISSION:
                processing_time = PROCESSING_TIME[task]
                if task == MEASUREMENT_REPORT:
                    self.counter.increment_UE_measurement()
                else:
                    self.counter.increment_UE_retransmit()
                ueid = msg['from']
                candidates = msg['candidate']
                UE = self.UEs[ueid]
                if self.connected(UE):
                    yield self.env.timeout(processing_time)
                if self.connected(UE):
                    # send the response to UE
                    data = {
                        "task": HANDOVER_REQUEST,
                        "ueid": ueid
                    }
                    # for now, just random. TODO
                    target_satellite_id = random.choice(candidates)
                    target_satellite = self.satellites[target_satellite_id]
                    self.env.process(
                        self.send_message(
                            delay=self.ISL_delay,
                            msg=data,
                            Q=target_satellite.messageQ,
                            to=target_satellite
                        )
                    )
            elif task == HANDOVER_ACKNOWLEDGE:
                processing_time = PROCESSING_TIME[task]
                self.counter.increment_satellite()
                satellite_id = msg['from']
                ueid = msg['ueid']
                UE = self.UEs[ueid]
                if self.connected(UE):
                    yield self.env.timeout(processing_time)
                if self.connected(UE):
                    data = {
                        "task": RRC_RECONFIGURATION,
                        "targets": [satellite_id],
                    }
                    self.env.process(
                        self.send_message(
                            delay=self.satellite_ground_delay,
                            msg=data,
                            Q=UE.messageQ,
                            to=UE
                        )
                    )
            elif task == HANDOVER_REQUEST:
                processing_time = PROCESSING_TIME[task]
                self.counter.increment_satellite()
                satellite_id = msg['from']
                ueid = msg['ueid']
                yield self.env.timeout(processing_time)
                data = {
                    "task": HANDOVER_ACKNOWLEDGE,
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
            elif task == RRC_RECONFIGURATION_COMPLETE:
                processing_time = PROCESSING_TIME[task]
                self.counter.increment_UE_RA()
                ue_id = msg['from']
                UE = self.UEs[ue_id]
                yield self.env.timeout(processing_time)
                data = {
                    "task": RRC_RECONFIGURATION_COMPLETE_RESPONSE,
                }
                self.env.process(
                    self.send_message(
                        delay=self.satellite_ground_delay,
                        msg=data,
                        Q=UE.messageQ,
                        to=UE
                    )
                )
                data2 = {
                    "task": PATH_SHIFT_REQUEST,
                }
                self.env.process(
                    self.send_message(
                        delay=self.core_delay,
                        msg=data2,
                        Q=self.AMF.messageQ,
                        to=self.AMF
                    )
                )
            elif task == GROUP_HANDOVER_NOTIFY:
                # Determine processing time and estimate if worth processing
                groupID = msg['groupID']
                left_x = msg['left_x']
                UE_list = self.group_count[groupID]
                processing_time = len(UE_list) * PROCESSING_TIME[PROCESS_ONE_UE]
                estimate_time = processing_time + self.satellite_ground_delay
                if estimate_time * self.velocity + self.position_x < left_x:
                    print(f"{self.type} {self.identity} notify group {groupID} at time {self.env.now}")
                    # TODO Do some logic here

            print(f"{self.type} {self.identity} finished processing msg:{msg} at time {self.env.now}")

    def update_position(self):
        """ Continuous updating the object location. """
        while True:
            yield self.env.timeout(1)  # Time between position updates
            # Update x and y based on velocity
            # Calculate time ratio
            ratio = 1 / 1000
            # direction set to right
            self.position_x += self.velocity * ratio

    # TODO The group information should be dynamic in real deployment.
    # Such update in real life should not cause delay, so, in our simulation, we update every ms.
    # TODO But accuracy may be affected
    def monitor_group_information(self):
        while True:
            yield self.env.timeout(1)
            group_info = {}
            for id in self.UEs:
                UE = self.UEs[id]
                if UE.serving_satellite is not None and UE.serving_satellite == self.identity and UE.state == ACTIVE:
                    groupID = UE.groupID
                    if groupID not in group_info:
                        group_info[groupID] = []
                    group_info[groupID].append(id)
            self.group_count = group_info
            for groupID in group_info:
                if groupID not in self.group_aggregators:
                    xy =  groupID.split('_')
                    x = int(xy[0])
                    y = int(xy[1])
                    ul, ru, rd, ld = utils.determine_edge_point(x, y, GROUP_AREA_L)
                    R = 24* 1000
                    if (self.cover_point_with_range(ru[0], ru[1], R)
                            and self.cover_point_with_range(rd[0], rd[1], R)
                            and ul[0] > self.position_x
                            and len(group_info[groupID])) >= min(self.hybrid_threshold, 3):
                        self.group_aggregators[groupID] = []
                        # Notify UEs and assign aggregators Task.
                        data = {
                            "task": GROUP_HANDOVER_NOTIFY,
                            "groupID": groupID,
                            "left_x": ul[0]
                        }
                        self.env.process(
                            self.send_message(
                                delay=0,
                                msg=data,
                                Q=self.messageQ,
                                to=self
                            )
                        )



    # ==================== Utils (Not related to Simpy) ==============
    def connected(self, UE):
        if UE.serving_satellite is None:
            return False
        else:
            return UE.serving_satellite.identity == self.identity
    def cover_point_with_range(self, pos_x, pos_y, R):
        d = math.sqrt(((pos_x - self.position_x) ** 2) + (
                (pos_y - self.position_y) ** 2))
        return d <= R
