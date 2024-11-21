

from schemas.navigation import WaypointTraitSymbol
from st_requests.market import get_market
from st_requests.waypoint import get_system

system = get_system('X1-Y3')
for wp in system.waypoints:
    if wp.has_trait(WaypointTraitSymbol.MARKETPLACE):
        print(wp.symbol)
        get_market(wp.symbol)
