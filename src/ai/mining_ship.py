
from asyncio import sleep
from typing import List, override
from ai.ship_controller import ShipController
from schemas.navigation import Waypoint
from schemas.ship import Ship, ShipNavStatus
from schemas.survey import Survey
from crud.waypoint import get_waypoint_with_symbol

class MinerShipController(ShipController):

    def __init__(self, ship: Ship, mine_waypoint: Waypoint, sell_waypoint: Waypoint, look_for: List[str]) -> None:
        super().__init__(ship)
        self.mine_waypoint = get_waypoint_with_symbol(mine_waypoint)
        self.sell_waypoint = get_waypoint_with_symbol(sell_waypoint)
        self.look_for = set(look_for)

    @override
    async def run(self) -> bool:
        self.ship.log("Miner Ship AI Enabled")
        self.busy = True
        surveys : List[Survey] = []
        while True:
            match self.ship.nav.status, self.ship.nav.waypointSymbol, self.ship.cooldown.time_remaining.total_seconds(), self.ship.cargo.capacity_remaining:
                case ShipNavStatus.IN_TRANSIT, _, _, _:
                    await sleep(self.ship.nav.route.time_remaining.total_seconds())
                case ShipNavStatus.IN_ORBIT, self.mine_waypoint.symbol, 0, c if c > 0:
                    if not surveys:
                        success, surveys = self.ship.survey()
                        sort_func = lambda x: x.rank_survey(self.look_for)
                        surveys = list(filter(sort_func ,surveys))
                        if surveys:
                            surveys.sort(key = sort_func, reverse=True)
                        self.ship.log(surveys)
                    else:
                        if survey := surveys[0]:
                            if not survey.is_valid:
                                surveys = []
                                continue
                        success, extraction = self.ship.extract(survey)
                        if success and extraction.yield_field.symbol not in self.look_for:
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
                    self.ship.log(self.ship.model_dump_json(indent=2),error=True)
                    return False
