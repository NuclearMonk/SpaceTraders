

from datetime import timedelta
from typing import List
from crud.job import assign_job, assign_miner_waypoint, get_miner_waypoint, get_miners_at_waypoint, get_ships_with_job
from crud.tradegood import get_good
from crud.waypoint import get_waypoints
from management.job import JobAssignment
from management.transport_manager import TransportManager, TransportOrder
from schemas.market import TradeSymbol
from schemas.navigation import WaypointTraitSymbol, WaypointType
from schemas.ship import Ship, ShipNavFlightMode, ShipNavStatus
from st_requests.ship import get_ship
from st_requests.waypoint import get_waypoint

MINEABLE_TRAITS = [WaypointTraitSymbol.COMMON_METAL_DEPOSITS,
                   WaypointTraitSymbol.RARE_METAL_DEPOSITS,
                   WaypointTraitSymbol.PRECIOUS_METAL_DEPOSITS,
                   WaypointTraitSymbol.MINERAL_DEPOSITS]

USELESS_GOODS = [get_good(TradeSymbol.ICE_WATER), get_good(
    TradeSymbol.QUARTZ_SAND), get_good(TradeSymbol.SILICON_CRYSTALS)]


class MiningManager():

    def __init__(self, transport_manager: TransportManager) -> None:
        self.drones = [get_ship(symbol)for symbol in get_ships_with_job(
            JobAssignment.MINING_DRONE)]
        self.drone_wps = {drone.symbol: get_waypoint(
            get_miner_waypoint(drone)) for drone in self.drones}
        self.setup_drones()
        self.awaiting_pickup = set()
        self.transport_manager = transport_manager

    def setup_drones(self):
        for drone in self.drones:
            assign_job(drone, JobAssignment.MINING_DRONE)
            if not self.drone_wps.get(drone.symbol):
                if wp := self.get_nearest_mineable_waypoint(drone):
                    assign_miner_waypoint(drone, wp)
                    self.drone_wps[drone.symbol] = get_waypoint(wp.symbol)

    def get_nearest_mineable_waypoint(self, ship: Ship):
        def dist(x): return x.distance_to(ship.nav.route.destination)
        wps = sorted(get_waypoints(trait_symbols=MINEABLE_TRAITS), key=dist)
        for wp in wps:
            if wp.type == WaypointType.ENGINEERED_ASTEROID:
                return wp
            if len(get_miners_at_waypoint(wp)) < 8:
                return wp
        return None

    def add_drone(self, ship: Ship) -> bool:
        if ship in self.drones:
            return False
        if wp := self.get_nearest_mineable_waypoint(ship):
            assign_job(ship, JobAssignment.MINING_DRONE)
            assign_miner_waypoint(ship, wp)
            self.drone_wps[ship.symbol] = wp.symbol
            self.drones.append(ship)
            return True
        return False

    def do_cycle(self) -> bool:
        for drone in self.drones:

            if drone.nav.live_status == ShipNavStatus.IN_TRANSIT:
                # skip in transit ships
                continue
            if drone.cooldown.time_remaining > timedelta(0):
                # skip ships whose cooldown is not up
                continue

            if drone.nav.live_status == ShipNavStatus.DOCKED:
                # drones should never dock anywhere so
                drone.orbit()
                return True
            # now we got drones in orbit with cooldown up
            if drone.nav.route.destination != self.drone_wps[drone.symbol]:
                # is not at the correct waypoint
                if drone.nav.flightMode == ShipNavFlightMode.DRIFT:
                    # we are in drift and in orbit, time to navigate
                    drone.navigate(self.drone_wps.get(drone.symbol))
                    return True
                drone.change_flight_mode(ShipNavFlightMode.DRIFT)
                return True

            # if we reach here then drone is at the correct location
            if drone.cargo.capacity_remaining == 0:
                if jettison_useless_cargo(drone):
                    # made new space
                    return True
                # cargo is full of useful items, must transfer to other ship
                else:
                    if drone.symbol in self.awaiting_pickup:
                        continue
                    else:
                        self.awaiting_pickup.add(drone.symbol)
                        for cargo_item in drone.cargo.inventory:
                            self.transport_manager.add_transport_order(
                                TransportOrder(cargo_item, cargo_item.units, drone.nav.route.destination, get_waypoint(
                                    'X1-Y3-H49'), pickup_ship=drone)
                            )
                    continue
            drone.extract()
            return True
        return False


def jettison_useless_cargo(drone: Ship) -> bool:
    for good in USELESS_GOODS:
        if units := drone.cargo.get_item_count(good.symbol):
            drone.jettison(good, units)
            return True

    return False
