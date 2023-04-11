from multiprocessing import Event, Queue, Process


prediction_array = []
NUM_OUTPUT = 1
NUM_FEATURES = 8
NUM_INPUT = NUM_FEATURES * 6
SAMPLE_SIZE = 40
SHOOT_MAX_TIME_LIMIT = 2
GRENADE_MAX_TIME_LIMIT = 6


beetleID_mapping = {
    1: "IMU1", #imu1
    2: "VEST1", #VEST1
    3: "GUN1", #GUN1
    4: "IMU2", #IMU2
    5: "VEST2", #vest2
    6: "GUN2", #gun2
    7: "TEST"
}

MQTT_USERNAME = "capstonekillingus"
MQTT_PASSWORD = "capstonekillingus"

imu_queue_p1 = Queue()
imu_queue_p2 = Queue()
action_p1_queue = Queue()
action_p2_queue = Queue()
viz_queue = Queue()
eval_queue = Queue()
intcomms_queue = Queue()
recv_queue = Queue()

processing = Event()
processing.clear()
grenadeP1Miss = Event()
grenadeP1Miss.clear()
grenadeP2Miss = Event()
grenadeP2Miss.clear()
grenadeP1Hit = Event()
grenadeP1Hit.clear()
grenadeP2Hit = Event()
grenadeP2Hit.clear()
shootP1Hit = Event()
shootP1Hit.clear()
shootP2Hit = Event()
shootP2Hit.clear()
relayFlag = Event()
relayFlag.set()
reloadSendRelayP1 = Event()
reloadSendRelayP1.clear() 
reloadSendRelayP2 = Event()
reloadSendRelayP2.clear()
evalServerConnected = Event()
evalServerConnected.set()

player_state = {
    "p1":
    {
        "hp": 100,
        "action": "none",
        "bullets": 6,
        "grenades": 2,
        "shield_time": 0,
        "shield_health": 0,
        "num_deaths": 0,
        "num_shield": 3
    },
    "p2":
    {
        "hp": 100,
        "action": "none",
        "bullets": 6,
        "grenades": 2,
        "shield_time": 0,
        "shield_health": 0,
        "num_deaths": 0,
        "num_shield": 3
    }
}

player_state_intcomms = {
    "p1":
    {
        "hp": 100,
        "action": "none",
        "bullets": 6,
    },
    "p2":
    {
        "hp": 100,
        "action": "none",
        "bullets": 6,
    }
}