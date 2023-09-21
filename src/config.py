# System level config
SATELLITE_R = 25 * 1000
NUMBER_UE = 10
SATELLITE_V = 7.56 * 1000
SATELLITE_GROUND_DELAY = 30
SATELLITE_SATELLITE_DELAY = 10
CORE_DELAY = 10
DURATION = 15000
RETRANSMIT = True
RETRANSMIT_THRESHOLD = 65
MAX_RETRANSMIT = 5
# Parameters
#TODO
# 1. The UEs will perform random access only the first time, which means the satellites will first goes to the massive UEs.
# 1.1 If restricting only one random access is weird, we can assign UEs during configuration.
# 2. Handover Decision should be set too.

# This labels the initial position of satellites
POS_SATELLITES = {
    1: (-25 * 1000, 0),
    2: (-35 * 1000, 0),
    3: (-45 * 1000, 0),
}

MEASUREMENT_REPORT = "MEASUREMENT_REPORT"
HANDOVER_REQUEST = "HANDOVER_REQUEST"
HANDOVER_ACKNOWLEDGE = "HANDOVER_ACKNOWLEDGE"
RRC_RECONFIGURATION = "RRC_RECONFIGURATION"
RRC_RECONFIGURATION_COMPLETE = "RRC_RECONFIGURATION_COMPLETE"
RRC_RECONFIGURATION_COMPLETE_RESPONSE = "RRC_RECONFIGURATION_COMPLETE_RESPONSE"
PATH_SHIFT_REQUEST = "PATH_SHIFT_REQUEST"
RETRANSMISSION = "RETRANSMISSION"

PROCESSING_TIME = {
    MEASUREMENT_REPORT: 0.5,
    HANDOVER_REQUEST: 0.5,
    HANDOVER_ACKNOWLEDGE: 0.1,
    RRC_RECONFIGURATION_COMPLETE: 0.1,
    PATH_SHIFT_REQUEST: 0.1,
    RETRANSMISSION: 0.1
}

SATELLITE_CPU = 1
UE_CPU = 4

'''
The below constants defined the state machine of UE
'''
# The UE is actively communicating with source base station
# and the UE has not made any action
ACTIVE = "ACTIVE"
# The UE sent the measurement report and waiting for configuration
WAITING_RRC_CONFIGURATION = "WAITING_RRC_CONFIGURATION"
# The UE lost the connection without being RRC configured
# MEANING that the UE failed to be handoff.
INACTIVE = "INACTIVE"
# The UE has received the RRC configuration message
RRC_CONFIGURED = "RRC_CONFIGURED"
# The UE has sent the random access request with RRC_RECONFIGURATION_COMPLETE
WAITING_RRC_RECONFIGURATION_COMPLETE_RESPONSE = "WAITING_RRC_RECONFIGURATION_COMPLETE_RESPONSE"

