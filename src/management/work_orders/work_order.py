

from asyncio import sleep
from typing import Any, Coroutine, List, Set, override
from crud.market import get_markets_exporting
from crud.waypoint import get_waypoint_with_symbol
from schemas.contract import Contract
from schemas.navigation import Waypoint
from schemas.ship import Ship, ShipNavStatus
from schemas.survey import Survey


class WorkOrder:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship

    def setup(self) -> bool:
        return True

    def cleanup(self) -> bool:
        return True

    async def run() -> bool:
        return True

    async def execute(self) -> bool:
        if not self.setup():
            return False
        if not await self.run():
            return False
        if not self.cleanup():
            return False
        return True


class TravelToWaypoint(WorkOrder):

    def __init__(self, ship: Ship, destination: Waypoint, dock: bool = False) -> None:
        self.destination = destination
        self.dock = dock
        super().__init__(ship)

    @override
    def setup(self) -> bool:
        return True

    async def run(self) -> Coroutine[Any, Any, bool]:
        return await self.ship.route_navigate(self.destination, self.dock)


class WaitFor(WorkOrder):
    def __init__(self, ship: Ship, t:int) -> None:
        super().__init__(ship)
        self.time = t
    async def run(self):
        await sleep(self.t)
        return True


class FulfillProcurementContract(WorkOrder):

    def __init__(self, ship: Ship, contract: Contract) -> None:
        self.contract = contract
        super().__init__(ship)

    @override
    def setup(self):
        self.ship.log("Procurement Contract Work Order Setup")
        self.good = self.contract.terms.deliver[0]
        self.delivery_waypoint = get_waypoint_with_symbol(
            self.good.destinationSymbol)

        markets = get_markets_exporting(self.good.tradeSymbol)
        if not markets:
            return False
        markets.sort(key=lambda x: self.delivery_waypoint.distance_to(
            get_waypoint_with_symbol(x.symbol)))
        self.purchase_waypoint = markets[0]
        self.units_to_deliver = self.good.unitsRequired - self.good.unitsFulfilled
        if self.units_to_deliver <= 0:
            return True
        if in_cargo := self.ship.cargo.items().get(self.good.tradeSymbol):
            self.units_to_pickup = self.units_to_deliver - in_cargo
        else:
            self.units_to_pickup = self.units_to_deliver
        for symbol, units in self.ship.cargo.items().items():
            if symbol != self.good.tradeSymbol:
                self.ship.jettison(symbol, units)
        return True

    async def run(self):
        while True:
            if self.units_to_deliver == 0:  # we delivered everything
                return True
            if self.ship.nav.status == ShipNavStatus.IN_TRANSIT:
                await sleep(self.ship.nav.route.time_remaining.total_seconds())
            # full cargo,or exact , head to destination
            if self.ship.cargo.capacity_remaining == 0 or self.ship.cargo.units == self.units_to_deliver:
                if not await self.ship.route_navigate(self.delivery_waypoint):
                    return False
                self.units_to_deliver -= self.ship.cargo.units
                if self.ship.nav.status != ShipNavStatus.DOCKED:
                    if not self.ship.dock():
                        return False
                if not self.ship.deliver_to_contract(
                        self.contract.id, self.good.tradeSymbol, self.ship.cargo.units):
                    return False
            else:
                if not await self.ship.route_navigate(self.purchase_waypoint):
                    return False
                if self.ship.nav.status != ShipNavStatus.DOCKED:
                    if not self.ship.dock():
                        return False
                batch_to_buy = self.units_to_pickup \
                    if self.units_to_pickup < self.ship.cargo.capacity_remaining \
                    else self.ship.cargo.capacity_remaining
                if not self.ship.purchase(self.good.tradeSymbol, batch_to_buy):
                    return False
                self.units_to_pickup -= batch_to_buy

    @override
    def cleanup(self):
        return self.contract.fulfill()


class MineUntilFull(WorkOrder):

    def __init__(self, ship: Ship, look_for: Set[str]) -> None:
        super().__init__(ship)
        self.look_for = look_for

    def setup(self) -> bool:
        return True

    def cleanup(self) -> bool:
        return True

    async def run(self) -> bool:
        surveys: List[Survey] = []
        while True:
            if not surveys:
                success, surveys = self.ship.survey()
                def sort_func(x): return x.rank_survey(self.look_for)
                surveys = list(filter(sort_func, surveys))
                if surveys:
                    surveys.sort(key=sort_func, reverse=True)
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
