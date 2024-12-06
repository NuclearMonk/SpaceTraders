

from datetime import timedelta
from typing import List, Optional
from crud.job import assign_job, assign_miner_waypoint, get_miner_waypoint, get_miners_at_waypoint, get_ships_with_job
from crud.tradegood import get_good
from crud.waypoint import get_waypoints
from management.job import JobAssignment
from management.miner import Miner
from management.transport_manager import TransportManager, TransportOrder
from schemas.market import TradeGood, TradeSymbol
from schemas.navigation import Waypoint, WaypointTraitSymbol, WaypointType
from schemas.ship import Ship, ShipNavFlightMode, ShipNavStatus
from st_requests.ship import get_ship
from st_requests.waypoint import get_waypoint

MINEABLE_TRAITS = [WaypointTraitSymbol.COMMON_METAL_DEPOSITS,
                   WaypointTraitSymbol.RARE_METAL_DEPOSITS,
                   WaypointTraitSymbol.PRECIOUS_METAL_DEPOSITS,
                   WaypointTraitSymbol.MINERAL_DEPOSITS]

USELESS_GOODS = [get_good(TradeSymbol.ICE_WATER), get_good(
    TradeSymbol.QUARTZ_SAND), get_good(TradeSymbol.SILICON_CRYSTALS)]

keep = {TradeSymbol.ALUMINUM_ORE,
        TradeSymbol.COPPER_ORE, TradeSymbol.IRON_ORE}


class MiningManager():

    def __init__(self, transport_manager: TransportManager) -> None:
        ships = [get_ship(symbol)for symbol in get_ships_with_job(
            JobAssignment.MINING_DRONE)]
        self.miners = [Miner(ship, self.__get_assigned_wp(ship), keep, self.request_pickup)
                       for ship in ships]
        self.transport_manager = transport_manager

    def __get_assigned_wp(self, ship: Ship) -> Optional[Waypoint]:
        if wp := get_miner_waypoint(ship):
            return get_waypoint(wp)
        return self. __get_nearest_mineable_waypoint(ship)

    def __get_nearest_mineable_waypoint(self, ship: Ship):
        def dist(x): return x.distance_to(ship.nav.route.destination)
        wps = sorted(get_waypoints(trait_symbols=MINEABLE_TRAITS), key=dist)
        for wp in wps:
            if wp.type == WaypointType.ENGINEERED_ASTEROID:
                return wp
            if len(get_miners_at_waypoint(wp)) < 8:
                return wp
        return None

    def request_pickup(self, ship: Ship, good: TradeGood, units: int):
        self.transport_manager.add_transport_order(TransportOrder(
            good,
            units,
            ship.nav.route.destination,
            get_waypoint('X1-Y3-H49'),
            pickup_ship=ship
        ))

    def add_miner(self, ship: Ship) -> bool:
        if ship in self.miners:
            return False
        if wp := self.__get_nearest_mineable_waypoint(ship):
            assign_job(ship, JobAssignment.MINING_DRONE)
            assign_miner_waypoint(ship, wp)
            self.miners.append(Miner(ship, self.__get_assigned_wp(ship), keep))
            return True
        return False

    def do_cycle(self) -> bool:
        for miner in self.miners:
            if miner.do_tick():
                return True
        return False
