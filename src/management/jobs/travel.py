

from management.jobs.job import Job
from pathfinding.pathfinding import calculate_route
from schemas.navigation import Waypoint
from schemas.ship import Ship, ShipNavStatus


class Travel(Job):

    def __init__(self, destination: Waypoint) -> None:
        self.destination = destination

    def start(self,ship: Ship):
        ship.log("Travel: Job Started")
        ship.log(f"Travel: Destination {self.destination}")
        ship.log(f"Travel: Calculating Route")

        if route := calculate_route(ship.nav.waypointSymbol, self.destination.symbol, ship.fuel.capacity, ship.fuel.current):
            self.route = route
            ship.log(f"Travel: Found Route\n"+ "\n".join(f"{wp.symbol} {refuel}" for wp, refuel in route))
            wp, refuel = self.route[0]
            if refuel:
                ship.log(f"Travel: Refueling")
                if ship.nav.status == ShipNavStatus.DOCKED:
                    ship.refuel()
                    ship.orbit()
                elif ship.nav.status == ShipNavStatus.IN_ORBIT:
                    ship.dock()
                    ship.refuel()
                    ship.orbit()
            elif ship.nav.status == ShipNavStatus.DOCKED:
                ship.orbit()
            return True
        ship.log(f"Travel: COULD NOT FIND ROUTE", error=True)

        return False

    async def work(self, ship: Ship):
        ship.log("Travel: Traveling")
        if len(self.route) > 1:
            for wp, refuel in self.route[1:-1]:
                ship.log(f"Travel: -> {wp.symbol}")
                await ship.navigate(wp)
                if refuel:
                    ship.log("Travel: Refueling")
                    ship.dock()
                    ship.refuel()
                    ship.orbit()
            wp, refuel = self.route[-1]
            ship.log(f"Travel: -> {wp.symbol}")
            await ship.navigate(wp)
            if refuel:
                ship.log("Travel: Refueling")
                ship.dock()
                ship.refuel()
                ship.orbit()
        return True

    def end(self,ship: Ship):
        ship.log("Travel: Arrived")
        return True
