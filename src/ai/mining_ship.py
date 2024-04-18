
from asyncio import sleep
from typing import List, override
from ai.ship_controller import ShipController
from navigation import WaypointSymbol, get_waypoint_with_symbol
from ship import Ship, ShipNavStatus


class MinerShipController(ShipController):

    def __init__(self, ship: Ship, mine_waypoint: WaypointSymbol, sell_waypoint: WaypointSymbol, keep: List[str]) -> None:
        super().__init__(ship)
        self.mine_waypoint = get_waypoint_with_symbol(mine_waypoint)
        self.sell_waypoint = get_waypoint_with_symbol(sell_waypoint)
        self.keep = set(keep)

    @override
    async def run(self):
        self.ship.log("Miner Ship AI Enabled")
        while True:
            match self.ship.nav.status, self.ship.nav.waypointSymbol, self.ship.cooldown.time_remaining.total_seconds(), self.ship.cargo.capacity_remaining:
                case ShipNavStatus.IN_TRANSIT, _, _, _:
                    await sleep(self.ship.nav.route.time_remaining.total_seconds())
                case ShipNavStatus.IN_ORBIT, self.mine_waypoint.symbol, 0, c if c > 0:
                    success, extraction = self.ship.extract()
                    if success and extraction.yield_field.symbol not in self.keep:
                        self.ship.jettison(
                            extraction.yield_field.symbol, extraction.yield_field.units)
                case ShipNavStatus.IN_ORBIT, self.mine_waypoint.symbol, t , c if c > 0:
                    await sleep(t)
                case ShipNavStatus.IN_ORBIT, self.mine_waypoint.symbol, _, 0:
                    await self.ship.navigate(self.sell_waypoint)
                case ShipNavStatus.IN_ORBIT, self.sell_waypoint.symbol, _, c if c > 0:
                    await self.ship.navigate(self.mine_waypoint)

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
                    return
