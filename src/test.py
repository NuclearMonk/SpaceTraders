

from crud.waypoint import get_waypoints, get_waypoint_with_symbol

from management.managers.mining import MiningManager
from schemas.ship import get_ship_list
ship = get_ship_list()[0]
mm = MiningManager()

mm.add_drone(ship)

