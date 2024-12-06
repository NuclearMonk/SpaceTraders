


from pathfinding.pathfinding import calculate_route
from schemas.navigation import Waypoint
from schemas.ship import Ship, ShipNavStatus


class Navigable:

    def __init__(self,ship: Ship, destination: Waypoint = None, status: ShipNavStatus = None) -> None:
        self.ship = ship
        self.destination : Waypoint = destination
        self.destination_status : ShipNavStatus = status
        if destination:
            self.route = calculate_route(self.ship.nav.route.destination, destination, self.ship.fuel.capacity, self.ship.engine.speed, self.ship.fuel.current, self.destination_status)
        else:
            self.route = None

    def set_destination(self, waypoint:Waypoint, status: ShipNavStatus):
        self.destination = waypoint
        self.destination_status = status
        self.route = calculate_route(self.ship.nav.route.destination, self.destination, self.ship.fuel.capacity, self.ship.engine.speed, self.ship.fuel.current)