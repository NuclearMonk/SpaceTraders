

import asyncio
from typing import Dict, List, Optional

from crud.waypoint import get_waypoint_with_symbol, get_waypoints
from management.routines.routine import Routine
from management.routines.wait import WaitForArrival
from management.ship_worker import ShipWorker
from schemas.navigation import Waypoint
from schemas.ship import Ship, ShipNavStatus


class MiningManager():

    def __init__(self) -> None:
        self.drones: List[ShipWorker] = []
        self.systems: Dict[str, MiningSystemManager] = {}

    def add_drone(self, ship: Ship) -> bool:

        system_symbol = ship.nav.systemSymbol
        drone = ShipWorker(ship)
        if system_symbol not in self.systems:
            self.systems[system_symbol] = MiningSystemManager(system_symbol)
        ms = self.systems[system_symbol]
        if not ms.add_drone(drone):
            return False
        self.drones.append(drone)
        return True


class MiningSystemManager:
    def __init__(self, system_symbol: str) -> None:
        self.symbol = system_symbol
        self.drones: List[ShipWorker] = []
        wps = get_waypoints(system_symbol, "ASTEROID")
        wps.extend(get_waypoints(system_symbol, "ENGINEERED_ASTEROID"))
        self.mineable_wps: List[Waypoint] = wps
        self.ships_per_wp: Dict[str: ShipWorker] = {
            wp.symbol: list() for wp in self.mineable_wps}
        self.drone_assignment : Dict[str: str] = {}

    def drones_assigned_to(self, wp_symbol: str) -> List[ShipWorker]:
        return self.ships_per_wp.get(wp_symbol, list())

    def assign_drone(self, drone: ShipWorker, waypoint_symbol: str):
        self.ships_per_wp[waypoint_symbol].append(drone)
        self.drone_assignment[drone.symbol] = waypoint_symbol

    def can_assign_drone(self, waypoint_symbol: str) -> bool:
        if waypoint_symbol not in self.ships_per_wp:
            return False
        if len(self.drones_assigned_to(waypoint_symbol)) > 8:
            return False
        return True

    def add_drone(self, drone: ShipWorker) -> bool:
        if drone.ship.nav.waypointSymbol not in self.ships_per_wp:
            return False
        if self.can_assign_drone(drone.ship.nav.waypointSymbol):
            self.drones.append(drone)
            self.assign_drone(drone, drone.ship.nav.waypointSymbol)
            return True
        wp = self.__get_nearest_available_wp(
            get_waypoint_with_symbol(drone.ship.nav.waypointSymbol))
        if not wp:
            return False
        self.drones.append(drone)
        self.assign_drone(drone, wp.symbol)
        return True

    def __get_nearest_available_wp(self, new_waypoint: Waypoint) -> Optional[Waypoint]:
        available_wps = filter(
            lambda x: self.can_assign_drone(x.symbol), self.mineable_wps)
        wps = sorted(available_wps, key=lambda x: x.distance_to(new_waypoint))
        if wps:
            return wps[0]
        return None
    
    def __get_next_routine(self, ship: Ship)-> Optional[Routine]:
        # weird edge case on boot up
        if ship.nav.status == ShipNavStatus.IN_TRANSIT:
            return WaitForArrival()

        # we are either in orbit somewhere or docked somewhere
        # we check if we in the wrong place
        if ship.nav.waypointSymbol != self.drone_assignment[ship.symbol]:
            #if we are in the wrong place we gotta drift
        

