
from typing import Iterable, List
from management.work_orders.work_order import MineUntilFull, TravelToWaypoint, WaitFor
from schemas.navigation import Waypoint
from schemas.ship import Ship, ShipNavStatus
from schemas.survey import Survey


class Job:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship


class Miner:

    def __init__(self, ship: Ship, mine_waypoint: Waypoint, sell_waypoint: Waypoint, look_for: Iterable[str]) -> None:
        super.__init__(ship)
        self.mine_waypoint = mine_waypoint
        self.sell_waypoint = sell_waypoint
        self.look_for = set(look_for)

    def __iter__(self):
        while True:
            match self.ship.nav.status, self.ship.nav.waypointSymbol, self.ship.cooldown.time_remaining.total_seconds(), self.ship.cargo.capacity_remaining:
                case ShipNavStatus.IN_TRANSIT, _, _, _:
                    yield WaitFor(self.ship, self.ship.nav.route.time_remaining.total_seconds())
                case ShipNavStatus.IN_ORBIT, self.mine_waypoint.symbol, 0, c if c > 0:
                    yield MineUntilFull(self.ship, self.look_for)
                case ShipNavStatus.IN_ORBIT, self.mine_waypoint.symbol, t, c if c > 0:
                    yield WaitFor(self.ship, t)
                case ShipNavStatus.IN_ORBIT, self.mine_waypoint.symbol, _, 0:
                    yield TravelToWaypoint(self.sell_waypoint, dock=True)
                case ShipNavStatus.IN_ORBIT, self.sell_waypoint.symbol, _, c if c > 0:
                    yield TravelToWaypoint(self.mine_waypoint)

                case ShipNavStatus.IN_ORBIT, self.sell_waypoint.symbol, _, 0:
                    self.ship.dock()
                case ShipNavStatus.DOCKED, self.sell_waypoint.symbol, _, 0:
                    good_names = list(self.ship.cargo.items().keys())
                    for good in good_names:
                        self.ship.sell(good)
                case ShipNavStatus.DOCKED, self.sell_waypoint.symbol, _, c if c > 0:
                    self.ship.refuel()
                    self.ship.orbit()
                case _:
                    print("ERROR")
                    print(self.ship.model_dump_json(indent=2))
                    return False
