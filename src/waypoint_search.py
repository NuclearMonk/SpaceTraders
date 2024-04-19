import argparse
import math
from utils import print_json
from dataclasses import dataclass




@dataclass
class WaypointSymbol:
    sector: str
    system: str
    waypoint: str = None





    def __str__(self) -> str:
        if self.waypoint:
            return self.waypoint_string
        else:
            return self.system_string






