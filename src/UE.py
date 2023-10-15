import math

import simpy

from Base import *
import utils
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
        self.timestamps = []

        self.messageQ = simpy.Store(env)
        self.cpus = simpy.Resource(env, UE_CPU)
        self.state = ACTIVE
        self.satellites = None
        self.UEs = None

        self.targetID = None
        self.retransmit_counter = 0

        self.groupID = None # Fixed
        self.share = None
        self.commitment_map = None
        self.threshold = None
        self.heads = None
        self.group_aggregation_map = {}


        # Running Process
        env.process(self.init())
        env.process(self.handle_messages())
        env.process(self.action_monitor())

    # =================== UE functions ======================
    def handle_messages(self):
        while True:
            msg = yield self.messageQ.get()
            print(f"{self.type} {self.identity} start handling msg:{msg} at time {self.env.now}, STATE: {self.state}")
            data = json.loads(msg)
            self.env.process(self.cpu_processing(data))

    def cpu_processing(self, msg):
        with self.cpus.request() as request:
            task = msg['task']
            if task == RRC_RECONFIGURATION:
                yield request
                satid = msg['from']
                # TODO one error once raised for serveing satellite is none
                # TODO the suspect reason is synchronization issue with "switch to inactive"
                # TODO Note that the UE didn't wait for the latest response for retransmission.
                if self.state == WAITING_RRC_CONFIGURATION and satid == self.serving_satellite.identity:
                    # get candidate target
                    targets = msg['targets']
                    # choose target
                    self.targetID = targets[0]
                    self.state = RRC_CONFIGURED
                    self.retransmit_counter = 0
                    print(f"{self.type} {self.identity} receives the configuration at {self.env.now}")
                    self.timestamps[-1]['timestamp'].append(self.env.now)
                    self.timestamps[-1]['isSuccess'] = True
                elif ((self.state == GROUP_WAITING_RRC_CONFIGURATION or self.state == GROUP_WAITING_RRC_CONFIGURATION_HEAD)
                     and satid == self.serving_satellite.identity):
                    targets = msg['targets']
                    # choose target
                    self.targetID = targets[0]
                    self.state = RRC_CONFIGURED
                    self.retransmit_counter = 0
            elif task == RRC_RECONFIGURATION_COMPLETE_RESPONSE:
                yield request
                satid = msg['from']
                satellite = self.satellites[satid]
                if self.covered_by(satid):
                    self.serving_satellite = satellite
                    self.state = ACTIVE
                    print(f"{self.type} {self.identity} finished handover at {self.env.now}")
            elif task == SWITCH_TO_GROUP_HANDOVER:
                yield request
                satid = msg['from']
                heads = msg['head']
                if self.state == ACTIVE and self.serving_satellite.identity == satid:
                    self.state = GROUP_ACTIVE
                    if self.identity in heads:
                        self.state = GROUP_ACTIVE_HEAD
                    self.share = msg['share']
                    self.commitment_map = msg['commitment_map']
                    self.threshold = msg['threshold']
                    self.heads = heads

            elif task == GROUP_AGGREGATION and self.state == GROUP_HEAD_AGGREGATING:
                yield request
                processing_time = PROCESSING_TIME[task]
                ue_id = msg['from']
                share = msg['share']
                commit = self.commitment_map[str(ue_id)]
                yield self.env.timeout(processing_time)
                if utils.verify_share_commitment(share, commit):
                    self.group_aggregation_map[ue_id] = share
                if len(self.group_aggregation_map) >= self.threshold:
                    candidates = []
                    for satid in self.satellites:
                        if self.covered_by(satid) and satid != self.serving_satellite.identity:
                            candidates.append(satid)
                    data = {
                        "task": GROUP_HANDOVER_MEASUREMENT,
                        "candidate": candidates,
                        "groupID": self.groupID,
                        "ticket": 'ticket' # TODO Without group handover ticket
                    }
                    if len(candidates) != 0 and self.state == GROUP_HEAD_AGGREGATING:
                        self.env.process(
                            self.send_message(
                                delay=self.satellite_ground_delay,
                                msg=data,
                                Q=self.serving_satellite.messageQ,
                                to=self.serving_satellite
                            )
                        )
                        self.state = GROUP_WAITING_RRC_CONFIGURATION_HEAD





    def action_monitor(self):
        while True:
            # send measurement report
            if self.state == ACTIVE and self.send_request_condition():
                candidates = []
                for satid in self.satellites:
                    if self.covered_by(satid) and satid != self.serving_satellite.identity:
                        candidates.append(satid)
                data = {
                    "task": MEASUREMENT_REPORT,
                    "candidate": candidates,
                }
                if len(candidates) != 0:
                    self.env.process(
                        self.send_message(
                            delay=self.satellite_ground_delay,
                            msg=data,
                            Q=self.serving_satellite.messageQ,
                            to=self.serving_satellite
                        )
                    )
                    self.timestamps.append({'timestamp': [self.env.now]})  # This is the start time
                    self.timestamps[-1]['from'] = self.serving_satellite.identity
                    self.timer = self.env.now
                    self.state = WAITING_RRC_CONFIGURATION
            if (self.state == GROUP_ACTIVE or self.state == GROUP_ACTIVE_HEAD) and self.group_broadcasting_condition(): # Broadcasting
                candidates = []
                for satid in self.satellites:
                    if self.covered_by(satid) and satid != self.serving_satellite.identity:
                        candidates.append(satid)
                if len(candidates) != 0:
                    if self.state == GROUP_ACTIVE:
                        self.state = GROUP_WAITING_RRC_CONFIGURATION
                    if self.state == GROUP_ACTIVE_HEAD:
                        self.state = GROUP_HEAD_AGGREGATING
                    data = {
                        'task': GROUP_AGGREGATION,
                        'share': self.share
                    }
                    for id in self.heads:
                        head = self.UEs[id]
                        self.env.process(
                            self.send_message(
                                delay=0,
                                msg=data,
                                Q=head.messageQ,
                                to=head
                            )
                        )

            # Retransmit
            if RETRANSMIT and self.state == WAITING_RRC_CONFIGURATION and self.env.now - self.timer > RETRANSMIT_THRESHOLD and self.retransmit_counter < MAX_RETRANSMIT:
                self.timer = self.env.now
                self.timestamps[-1]['timestamp'].append(self.env.now)  # retransmission time
                candidates = []
                for satid in self.satellites:
                    if self.covered_by(satid) and satid != self.serving_satellite.identity:
                        candidates.append(satid)
                data = {
                    "task": RETRANSMISSION,
                    "candidate": candidates
                }
                if len(candidates) != 0:
                    self.env.process(
                        self.send_message(
                            delay=self.satellite_ground_delay,
                            msg=data,
                            Q=self.serving_satellite.messageQ,
                            to=self.serving_satellite
                        )
                    )
                    self.retransmit_counter += 1
            # send random access request
            if self.state == RRC_CONFIGURED:  # When the UE has the configuration
                if self.targetID and self.covered_by(self.targetID):  # The condition can be added here
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
                    self.state = WAITING_RRC_RECONFIGURATION_COMPLETE_RESPONSE
            if self.state in [GROUP_ACTIVE,GROUP_ACTIVE_HEAD,GROUP_WAITING_RRC_CONFIGURATION,GROUP_WAITING_RRC_CONFIGURATION_HEAD ,GROUP_HEAD_AGGREGATING] and self.terminate_group_handover():
                self.state = ACTIVE
            # switch to inactive
            if self.serving_satellite is not None and self.outside_coverage():
                print(
                    f"UE {self.identity} lost connection at time {self.env.now} from satellite {self.serving_satellite.identity}")
                self.serving_satellite = None
                if self.state == ACTIVE or self.state == WAITING_RRC_CONFIGURATION or self.state in [GROUP_ACTIVE,GROUP_ACTIVE_HEAD,GROUP_WAITING_RRC_CONFIGURATION,GROUP_WAITING_RRC_CONFIGURATION_HEAD ,GROUP_HEAD_AGGREGATING]:
                    if self.state == WAITING_RRC_CONFIGURATION:
                        print(f"UE {self.identity} handover failure at time {self.env.now}")
                        self.timestamps[-1]['timestamp'].append(self.env.now)
                        self.timestamps[-1]['isSuccess'] = False
                    self.state = INACTIVE
            yield self.env.timeout(1)

    # ==================== Utils (Not related to Simpy) ==============
    def covered_by(self, satelliteID):
        satellite = self.satellites[satelliteID]
        d = math.sqrt(((self.position_x - satellite.position_x) ** 2) + (
                (self.position_y - satellite.position_y) ** 2))
        return d <= SATELLITE_R

    def send_request_condition(self):
        p = (self.position_x, self.position_y)
        d1_serve = math.dist(p, (self.serving_satellite.position_x, self.serving_satellite.position_y))
        for satid in self.satellites:
            satellite = self.satellites[satid]
            d = math.dist(p, (satellite.position_x, satellite.position_y))
            if d + 100 < d1_serve:
                return True
        return False

    def outside_coverage(self):
        p = (self.position_x, self.position_y)
        d1_serve = math.dist(p, (self.serving_satellite.position_x, self.serving_satellite.position_y))
        # TODO We may want to remove the second condition someday...
        return d1_serve >= SATELLITE_R and self.position_x < self.serving_satellite.position_x

    def group_broadcasting_condition(self):
        return self.send_request_condition()

    def terminate_group_handover(self):
        p = (self.position_x, self.position_y)
        d1_serve = math.dist(p, (self.serving_satellite.position_x, self.serving_satellite.position_y))
        return d1_serve >= 24*1000 and self.position_x < self.serving_satellite.position_x
