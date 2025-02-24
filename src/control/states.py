from enum import Enum, auto

class States(Enum):
    CROSSWALK = auto()
    STOP_INTERSECTION = auto()
    PRIORITY_INTERSECTION = auto()
    LANE_KEEPING = auto()
    HIGHWAY = auto()
    PARKING = auto()
    HIGHWAY_EXIT = auto()
    ROUND_ABOUT = auto()