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
from st_requests.ship import get_ship
from st_requests.waypoint import get_waypoint
from state_machine.states.sm_travel import SMTravel

miner = Miner(get_ship('SHOCSOARES-1'), get_waypoint('X1-Y3-B32'), keep= mining_manager.keep)
# for step in navigable.route.steps:
#     print(step)
# while True:
#     sleep(0.5)
#     sm.do_tick()

print(miner.state_machine.viz())