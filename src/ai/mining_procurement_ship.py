
from asyncio import sleep
from typing import List, override
from ai.ship_controller import ShipController
from schemas.contract import Contract
from schemas.navigation import Waypoint
from schemas.ship import Ship, ShipNavStatus
from schemas.survey import Survey
from crud.waypoint import get_waypoint_with_symbol

class ProcurementMinerController(ShipController):

    def __init__(self, ship: Ship, mine_waypoint: Waypoint, contract: Contract) -> None:
        super().__init__(ship)
        self.mine_waypoint = get_waypoint_with_symbol(mine_waypoint)
        self.delivery_waypoint = get_waypoint_with_symbol(contract.terms.deliver[0].destinationSymbol)
        self.look_for = set([good.tradeSymbol for good in contract.terms.deliver])
        self.contract = contract

    @override
    async def run(self):
        self.ship.log("Contract Fulfillment Miner Ship AI Enabled")
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
                        surveys = sorted(filter(sort_func ,surveys), key = sort_func, reverse=True)
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
                    await self.ship.navigate(self.delivery_waypoint)
                case ShipNavStatus.IN_ORBIT, self.delivery_waypoint.symbol, _, c if c > 0:
                    await self.ship.navigate(self.mine_waypoint)

                case ShipNavStatus.IN_ORBIT, self.delivery_waypoint.symbol, _, 0:
                    self.ship.dock()
                case ShipNavStatus.DOCKED, self.delivery_waypoint.symbol, _, 0:
                    for good_name, units in self.ship.cargo.items().items():
                        self.contract = self.ship.deliver_to_contract(self.contract.id, good_name, units)

                case ShipNavStatus.DOCKED, self.delivery_waypoint.symbol, _, c if c > 0:
                    self.ship.refuel()
                    self.ship.orbit()
                case _:
                    self.ship.log(self.ship.model_dump_json(indent=2),error=True)
                    return
