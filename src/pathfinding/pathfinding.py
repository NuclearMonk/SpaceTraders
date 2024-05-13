


from typing import List, Optional

from schemas.navigation import Waypoint
from crud import get_waypoints_in_system

def in_system_pathfinding(start: str, destination: str, waypoints: List[Waypoint])-> Optional[List[Waypoint]]: 
    distances = {wp.symbol: float("inf") for wp in waypoints}
    fuel_remaining = {wp.symbol: 0 for wp in waypoints}
    previous = {wp.symbol: None for wp in waypoints}
    markets = set()
    for wp in waypoints:
        trait_symbols = (trait.symbol for trait in wp.traits)
        if "MARKETPLACE" in trait_symbols:
            markets.add(wp.symbol) 
    
    print(markets)


in_system_pathfinding("","", get_waypoints_in_system("X1-U25"))