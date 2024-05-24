

from heapq import heappop, heappush
from math import sqrt
from typing import List, Optional

from crud.waypoint import get_waypoint_with_symbol
from schemas.navigation import Waypoint
from crud import get_waypoints_in_system
from utils.utils import system_symbol_from_wp_symbol


class PathFindingWaypoint:
    __slots__ = ["symbol", "x", "y",
                 "has_marketplace", "nearest_market_distance"]

    def __init__(self, symbol, x, y, has_marketplace, nearest_market_distance=float("inf")):
        self.symbol = symbol
        self.x = x
        self.y = y
        self.has_marketplace = has_marketplace
        self.nearest_market_distance = nearest_market_distance


def fuel_cost(A: PathFindingWaypoint, B: PathFindingWaypoint):
    if A == B:
        return 0
    x = round(sqrt((A.x-B.x)**2 + (A.y-B.y)**2))
    if x == 0:
        return 1
    return x


def create_graph(waypoints: List[Waypoint])-> Dict[str, PathFindingWaypoint]:
    wps = {wp.symbol: PathFindingWaypoint(
        wp.symbol, wp.x, wp.y, wp.has_trait("MARKETPLACE")) for wp in waypoints}
    markets = [v for v in wps.values() if v.has_marketplace]
    for v in wps.values():
        markets.sort(key=lambda x: fuel_cost(v, x))
        v.nearest_market_distance = fuel_cost(v, markets[0])
    return wps


def dijkstra_with_fuel(start: str, destination: str, waypoints: List[Waypoint], max_fuel: int, starting_fuel: int) -> Optional[List[Waypoint]]:
    distances = {}
    previous = {}
    fuel = {}
    wps = create_graph(waypoints)
    heap = []
    if wps[start].has_marketplace:
        heappush(heap, (0, max_fuel, start, None, True))
    else:
        heappush(heap, (0, starting_fuel, start, None, False))
    while heap:
        dist, fuel_remaining, symbol, prev, refuel = heappop(heap)
        if symbol in distances:
            continue  # we visited it before

        distances[symbol] = dist
        previous[symbol] = prev
        fuel[symbol] = refuel
        if symbol == destination:
            return previous, distances, fuel
        for neighbor in wps.values():
            if neighbor.symbol == symbol:  # skip ourselves
                continue
            if neighbor.symbol not in distances:  # if we havent visited this neighbour yet
                # check if we can travel to it
                if fuel_cost(wps[symbol], neighbor) < fuel_remaining:
                    if neighbor.has_marketplace:  # then we refuel on arrival making current fuel = max_fuel
                        heappush(
                            heap, (dist + fuel_cost(wps[symbol], neighbor), max_fuel, neighbor.symbol, symbol, True))
                    # and if we aint gonna be stranded afterwards
                    elif neighbor.nearest_market_distance <= fuel_remaining - fuel_cost(
                            wps[symbol], neighbor):
                        # otherwise, we consume some fuel instead and travel to it
                        heappush(heap, (dist + fuel_cost(wps[symbol], neighbor), fuel_remaining - fuel_cost(
                            wps[symbol], neighbor), neighbor.symbol, symbol, False))

    return previous, distances, fuel


def calculate_route(start: str, destination: str, max_fuel: int, starting_fuel: int) -> Optional[List[str]]:
    start_system = system_symbol_from_wp_symbol(start)
    destination_system = system_symbol_from_wp_symbol(destination)
    if start_system == destination_system:
        waypoints = get_waypoints_in_system(start_system)
        previous, distances, refuel = dijkstra_with_fuel(
            start, destination, waypoints, max_fuel, starting_fuel)
        if destination in previous:
            current = destination
            route = []
            while current != None:
                route.append(
                    (get_waypoint_with_symbol(current), refuel[current]))
                current = previous[current]
            route.reverse()
    return route
