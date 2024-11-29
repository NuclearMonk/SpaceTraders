

from heapq import heappop, heappush
from itertools import product
from math import sqrt
from typing import Dict, List, Optional

from crud.waypoint import get_waypoint_with_symbol, get_waypoints
from schemas.navigation import Waypoint
from schemas.ship import ShipNavFlightMode
from st_requests.waypoint import get_waypoint
from utils.utils import system_symbol_from_wp_symbol


class PathFindingWaypoint:
    __slots__ = ['symbol', 'x', 'y',
                 'has_marketplace']

    def __init__(self, symbol, x, y, has_marketplace, nearest_market_distance=float('inf')):
        self.symbol = symbol
        self.x = x
        self.y = y
        self.has_marketplace = has_marketplace


class PathfindingEdge:
    __slots__ = ['start', 'end', 'flight_mode',
                 'refuel', 'cost_time', 'cost_fuel']

    def __init__(self, start: PathFindingWaypoint,
                 end: PathFindingWaypoint,
                 flight_mode: ShipNavFlightMode, refuel: bool, ship_engine_speed) -> None:
        self.start = start
        self.end = end
        self.flight_mode = flight_mode
        self.refuel = refuel
        self.cost_fuel = fuel_cost(start, end, flight_mode)
        self.cost_time = time_cost(start, end, flight_mode, ship_engine_speed)

    def __lt__(self, other):
        if self.cost_time<other.cost_time:
            return True
        if self.cost_fuel<other.cost_fuel:
            return True
        if self.refuel and not other.refuel:
            return True
        return False

class RouteStep:
    
    def __init__(self, edge: PathfindingEdge) -> None:
        self.start = get_waypoint(edge.start.symbol)
        self.end = get_waypoint(edge.end.symbol)
        self.flight_mode = edge.flight_mode
        self.refuel = edge.refuel
        self.time = edge.cost_time
        
class PathfindingRoute:
    def __init__(self, edges: List[PathfindingEdge]) -> None:
        self.steps = [RouteStep(edge) for edge in edges]
        self.total_time= sum(step.time for step in self.steps)
        

def fuel_cost(A: PathFindingWaypoint, B: PathFindingWaypoint, flight_mode: ShipNavFlightMode):
    if A == B:
        return 0
    match flight_mode:
        case ShipNavFlightMode.BURN:
            return 2 * max(1, round(sqrt((A.x-B.x)**2 + (A.y-B.y)**2)))
        case ShipNavFlightMode.CRUISE:
            return max(1, round(sqrt((A.x-B.x)**2 + (A.y-B.y)**2)))
        case ShipNavFlightMode.STEALTH:
            return max(1, round(sqrt((A.x-B.x)**2 + (A.y-B.y)**2)))
        case ShipNavFlightMode.DRIFT:
            return 1


def time_cost(A: PathFindingWaypoint, B: PathFindingWaypoint, flight_mode: ShipNavFlightMode, engine_speed: int):
    dist = max(1, round(sqrt((A.x-B.x)**2 + (A.y-B.y)**2)))
    match flight_mode:
        case ShipNavFlightMode.BURN:
            return round(dist*(12.5/engine_speed)+15)
        case ShipNavFlightMode.CRUISE:
            return round(dist*(25/engine_speed)+15)
        case ShipNavFlightMode.STEALTH:
            return round(dist*(30/engine_speed)+15)
        case ShipNavFlightMode.DRIFT:
            return round(dist*(250/engine_speed)+15)


def create_nodes(waypoints: List[Waypoint]) -> Dict[str, PathFindingWaypoint]:
    wps = {wp.symbol: PathFindingWaypoint(
        wp.symbol, wp.x, wp.y, wp.has_trait('MARKETPLACE')) for wp in waypoints}
    return wps


def create_edges(waypoints: List[PathFindingWaypoint], max_fuel: int, ship_engine_speed: int) -> Dict[str, List[PathfindingEdge]]:
    edges = {wp.symbol: list() for wp in waypoints}
    for start, end in product(waypoints, waypoints):
        if start == end:
            continue
        edges[start.symbol].append(
            PathfindingEdge(start, end, ShipNavFlightMode.DRIFT,
                            False, ship_engine_speed))
        edge = PathfindingEdge(
            start, end, ShipNavFlightMode.CRUISE, False, ship_engine_speed)
        if edge.cost_fuel < max_fuel:
            edges[start.symbol].append(edge)

        if start.has_marketplace:
            edges[start.symbol].append(
                PathfindingEdge(start, end, ShipNavFlightMode.DRIFT,
                                True, ship_engine_speed))
            edge = PathfindingEdge(
                start, end, ShipNavFlightMode.CRUISE, True, ship_engine_speed)
            if edge.cost_fuel < max_fuel:
                edges[start.symbol].append(edge)
    return edges


def djikstras(start: str, destination: str, waypoints: List[Waypoint], max_fuel: int, engine_speed: int, starting_fuel: int, ):
    distances = {}
    times = {}
    wps = create_nodes(waypoints)
    routes = {}
    edges = create_edges(wps.values(), max_fuel, engine_speed)
    heap = []
    heappush(heap, (0, 0, starting_fuel, start, None))
    while heap:
        time, dist, fuel_remaining, symbol, edge = heappop(heap)
        if symbol in distances:
            continue  # we visited it before

        distances[symbol] = dist
        routes[symbol] =edge
        times[symbol] = time
        if symbol == destination:
            return distances, times, routes
        for edge in edges[symbol]:
            neighbor = edge.end
            if neighbor.symbol not in times:  # if we havent visited this neighbour yet
                # check if we can travel to it
                if edge.refuel:
                    fuel_remaining = max_fuel
                if edge.cost_fuel < fuel_remaining:
                    # otherwise, we consume some  instead and travel to it
                    heappush(heap, (time+edge.cost_time, dist + edge.cost_fuel,
                             fuel_remaining - edge.cost_fuel, neighbor.symbol, edge))
            elif times[neighbor.symbol] < time + edge.cost_time and edge.cost_fuel < fuel_remaining:
                heappush(heap, (time+edge.cost_time, dist + edge.cost_fuel,
                                fuel_remaining - edge.cost_fuel, neighbor.symbol, edge))

    return  distances, times, routes


def dijkstra_with_fuel(start: str, destination: str, waypoints: List[Waypoint], max_fuel: int, starting_fuel: int) -> Optional[List[Waypoint]]:
    distances = {}
    previous = {}
    fuel = {}
    wps = create_nodes(waypoints)
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
        fuel[symbol] = refuelfuel
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


def calculate_route(start: str, destination: str, max_fuel: int,engine_speed: int, starting_fuel: int) -> Optional[List[tuple[Waypoint, bool]]]:
    start_system = system_symbol_from_wp_symbol(start)
    destination_system = system_symbol_from_wp_symbol(destination)
    if start_system == destination_system:
        if start == destination:
            return None
        waypoints = get_waypoints(system_symbol=start_system)
        distances, times, routes = djikstras(
            start, destination, waypoints, max_fuel,engine_speed, starting_fuel)

        if destination in routes:
            current = destination
            route = []
            while routes[current] != None:
                print(current)
                print(routes[current].start.symbol)
                route.append(routes[current])
                current = routes[current].start.symbol
            route.reverse()
            return PathfindingRoute(route)
    return None
