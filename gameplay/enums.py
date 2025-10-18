from enum import Enum




class State(Enum):
    ZOMBIE = "zombie"
    HEALTHY = "healthy"
    INJURED = "injured"
    CORPSE = "corpse"


class HumanType(Enum):
    DEFAULT = "default"
    BUSINESS = "business"
    DOCTOR = "doctor"
    ELDERLY = "elderly"
    POLICE = "police"


class ActionState(Enum):
    SAVE = 'save'
    SQUISH = 'squish'
    SKIP = 'skip'
    SCRAM = 'scram'
   
class ActionCost(Enum):
    SAVE = 0
    SQUISH = 0
    SKIP = 0
    SCRAM = 0


class Points(Enum):
    SAVE = 10
    SQUISH = 10
    SKIP = 10
    SCRAM = 0

#easter egg beaver

class Multiplier(Enum):
    BUSINESS = 5
    DOCTOR = 7
    ELDERLY = 3
    POLICE = 6
