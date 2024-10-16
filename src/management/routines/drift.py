

from management.routines.routine import Routine
from schemas.navigation import Waypoint
from schemas.ship import Ship, ShipNavFlightMode, ShipNavStatus


class Drift(Routine):

    def __init__(self, destination: Waypoint) -> None:
        self.destination = destination


    def start(self,ship: Ship):
        ship.log("Drift: Job Started")
        ship.log(f"Drift: Destination {self.destination}")
        if ship.nav.flightMode != ShipNavFlightMode.DRIFT:
            self.og_flight_mode = ship.nav.flightMode
            ship.change_flight_mode(ShipNavFlightMode.DRIFT)
        else: 
            self.og_flight_mode = ship.nav.flightMode

        if ship.nav.status == ShipNavStatus.DOCKED:
            ship.orbit()
        
    async def work(self, ship: Ship):
        ship.log("Drift: Traveling")
        return await ship.navigate(self.destination)
    
    def end(self, ship: Ship):
        if ship.nav.flightMode != self.og_flight_mode:
            ship.change_flight_mode(self.og_flight_mode)
        ship.log("Drift: Done")
        return True