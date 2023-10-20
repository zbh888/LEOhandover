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
        self.message_from_UE_group_measurement = 0
        self.message_from_UE_retransmit = 0
        self.message_from_UE_group_retransmit = 0
        self.message_from_UE_RA = 0
        self.message_from_satellite = 0
        self.message_from_AMF = 0

        self.dropped_message_from_non_group = 0
        self.dropped_message_from_group = 0

    def increment_UE_measurement(self):
        self.total_messages += 1
        self.message_from_UE_measurement += 1

    def increment_UE_group_measurement(self):
        self.total_messages += 1
        self.message_from_UE_group_measurement += 1

    def increment_UE_retransmit(self):
        self.total_messages += 1
        self.message_from_UE_retransmit += 1

    def increment_UE_group_retransmit(self):
        self.total_messages += 1
        self.message_from_UE_group_retransmit += 1

    def increment_satellite(self):
        self.total_messages += 1
        self.message_from_satellite += 1

    def increment_UE_RA(self):
        self.total_messages += 1
        self.message_from_UE_RA += 1

    def increment_AMF(self):
        self.total_messages += 1
        self.message_from_AMF += 1

    def increment_dropped_from_group(self):
        self.dropped_message_from_group += 1

    def increment_dropped_from_nongroup(self):
        self.dropped_message_from_non_group += 1


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
        self.group_info = {}
        self.group_sending_time = {} # To avoid send duplicate tasks
        self.stored_notified_group_member = {} # This is the record UEs that notified
        self.group_aggregators = {} # This ensures only one task to notify UEs
        self.group_share_commit = {}
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
            if task == MEASUREMENT_REPORT: self.counter.increment_UE_measurement()
            if task == RETRANSMISSION: self.counter.increment_UE_retransmit()
            if task == HANDOVER_ACKNOWLEDGE or task == GROUP_HANDOVER_REQUEST or task == HANDOVER_REQUEST or task == GROUP_HANDOVER_ACKNOWLEDGE:
                self.counter.increment_satellite()
            if task == RRC_RECONFIGURATION_COMPLETE: self.counter.increment_UE_RA()
            if task == GROUP_HANDOVER_MEASUREMENT: self.counter.increment_UE_group_measurement()
            if task == GROUP_RETRANSMISSION: self.counter.increment_UE_group_retransmit()
            if task == AMF_RESPONSE: self.counter.increment_AMF()


            if task == MEASUREMENT_REPORT or task == RETRANSMISSION:
                if len(self.cpus.queue) < QUEUED_SIZE:
                    print(f"{self.type} {self.identity} accepted msg:{msg} at time {self.env.now}")
                    self.env.process(self.cpu_processing(msg=data, priority=3))
                else:
                    self.counter.increment_dropped_from_nongroup()
                    print(f"{self.type} {self.identity} dropped msg:{msg} at time {self.env.now}")
            elif task == GROUP_HANDOVER_MEASUREMENT or task == GROUP_RETRANSMISSION:
                if len(self.cpus.queue) < QUEUED_SIZE:
                    print(f"{self.type} {self.identity} accepted msg:{msg} at time {self.env.now}")
                    self.env.process(self.cpu_processing(msg=data, priority=2))
                else:
                    self.counter.increment_dropped_from_group()
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
                    "previous_id": msg['previous_id']
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
                number_aggregator = 3
                groupID = msg['groupID']
                left_x = msg['left_x']
                UE_list = msg['ue_list']
                processing_time = PROCESSING_TIME[PREPARE_SIGNATURE] + number_aggregator * PROCESSING_TIME[NOTIFY_AGGREGATOR]
                estimate_time = processing_time + self.satellite_ground_delay
                ratio = 1 / 1000
                if ratio * estimate_time * self.velocity + self.position_x < left_x:
                    yield self.env.timeout(processing_time)
                    aggregatorIDs = random.sample(UE_list, number_aggregator)
                    print(f"{self.type} {self.identity} notifies group {groupID} at time {self.env.now}")
                    ID_commitment = {}
                    for ueID in UE_list:
                        UE = self.UEs[ueID]
                        if self.connected(UE):
                            share = utils.generate_share()
                            commit = utils.generate_commitment(share)
                            self.group_share_commit[ueID] = (share, commit)
                            ID_commitment[ueID] = commit
                        else:
                            print("ERROR This shouldn't happen")
                    self.stored_notified_group_member[groupID] = UE_list
                    threshold = len(UE_list) // 2 + 1
                    #self.group_aggregators[groupID] = aggregatorIDs
                    for ueID in UE_list:
                        UE = self.UEs[ueID]
                        share = self.group_share_commit[ueID][0]
                        commit = self.group_share_commit[ueID][1]
                        data = {
                            "task": SWITCH_TO_GROUP_HANDOVER,
                            "share": share,
                            "commit": commit,
                            "head": aggregatorIDs,
                            "commitment_map": ID_commitment,
                            "threshold": threshold,  #TODO This needs some change
                        }
                        self.env.process(
                            self.send_message(
                                delay=self.satellite_ground_delay,
                                msg=data,
                                Q=UE.messageQ,
                                to=UE
                            )
                        )
            elif task == GROUP_HANDOVER_MEASUREMENT or task == GROUP_RETRANSMISSION:
                ticket = msg['ticket']
                groupID = msg['groupID']
                UEList = self.stored_notified_group_member[groupID]
                # TODO Verify the ticket [Will not Implement]
                if ticket == "ticket":
                    processing_time = PROCESSING_TIME[task]
                    previous_time = 0
                    if groupID in self.group_sending_time:
                        previous_time = self.group_sending_time[groupID]
                    difference = self.env.now - previous_time
                    if difference > 1:
                        self.group_sending_time[groupID] = self.env.now
                    # TODO We need to verify geometric information to see if this task worth processing.
                        yield self.env.timeout(processing_time)
                        candidates = msg['candidate']
                        target_satellite_id = random.choice(candidates)
                        target_satellite = self.satellites[target_satellite_id]
                        data = {
                            "task": GROUP_HANDOVER_REQUEST,
                            "ue_list": UEList,
                        }
                        self.env.process(
                            self.send_message(
                                delay=self.ISL_delay,
                                msg=data,
                                Q=target_satellite.messageQ,
                                to=target_satellite
                            )
                        )

            elif task == GROUP_HANDOVER_REQUEST:
                UE_list = msg['ue_list']
                processing_time = PROCESSING_TIME[task]
                satellite_id = msg['from']
                yield self.env.timeout(processing_time)
                data = {
                    "task": GROUP_HANDOVER_ACKNOWLEDGE,
                    "ue_list": UE_list
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
            elif task == GROUP_HANDOVER_ACKNOWLEDGE:
                UE_list = msg['ue_list']
                processing_time = PROCESSING_TIME[task]
                yield self.env.timeout(processing_time)
                satellite_id = msg['from']
                for ue_id in UE_list:
                    UE = self.UEs[ue_id]
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
            elif task == AMF_RESPONSE:
                processing_time = PROCESSING_TIME[AMF_RESPONSE]
                yield self.env.timeout(processing_time)

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
            yield self.env.timeout(10)
            # This records the ACTIVE UEs within the coverage
            group_info = {}
            for id in self.UEs:
                UE = self.UEs[id]
                if self.connected(UE) and UE.state == ACTIVE:
                    groupID = UE.groupID
                    if groupID not in group_info:
                        group_info[groupID] = []
                    group_info[groupID].append(id)
            self.group_info = group_info
            for groupID in group_info:
                if groupID not in self.group_aggregators:
                    xy =  groupID.split('_')
                    x = int(xy[0])
                    y = int(xy[1])
                    ul, ru, rd, ld = utils.determine_edge_point(x, y, GROUP_AREA_L)
                    R = 0.9 * SATELLITE_R # TODO This parameter means some UEs must random access in time.
                    if (self.cover_point_with_range(ru[0], ru[1], R)
                            and self.cover_point_with_range(rd[0], rd[1], R)
                            and ul[0] > self.position_x
                            and len(group_info[groupID])) >= self.hybrid_threshold:
                        self.group_aggregators[groupID] = []
                        # Notify UEs and assign aggregators Task.
                        data = {
                            "task": GROUP_HANDOVER_NOTIFY,
                            "groupID": groupID,
                            "left_x": ul[0],
                            "ue_list": group_info[groupID]
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
