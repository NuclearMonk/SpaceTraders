# from schemas.navigation import WaypointTraitSymbol
# from st_requests.market import get_market
# from st_requests.waypoint import get_system

# system = get_system('X1-Y3')
# for wp in system.waypoints:
#     if wp.has_trait(WaypointTraitSymbol.MARKETPLACE):
#         print(wp.symbol)
#         get_market(wp.symbol)


from time import sleep
from management import mining_manager
from management.miner import Miner
from management.navigable import Navigable
from pathfinding.pathfinding import calculate_route
from schemas.ship import ShipNavStatus
from st_requests.contract import get_open_contracts
from st_requests.ship import get_ship
from st_requests.waypoint import get_waypoint
from state_machine.states.sm_travel import SMTravel
from utils.utils import utcnow

print(*((c.id, c.accepted, c.fulfilled, c.deadlineToAccept>utcnow()) for c in get_open_contracts()),sep='\n')