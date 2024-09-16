

import asyncio
from enum import StrEnum
from typing import Dict
from ai.ship_controller import ShipController
from management.work_orders.work_order import FulfillProcurementContract
from schemas.contract import get_open_contracts
from schemas.ship import Ship, get_ship_list
from logging import getLogger
logger = getLogger(__name__)


class ShipRoles(StrEnum):
    CONTRACTOR = "Contractor"


class FleetManager():
    def __init__(self) -> None:
        logger.info("STARTING MANAGER")
        self.ships: Dict[str, Ship] = {
            ship.symbol: ship for ship in get_ship_list()}
        self.roles = {"SHOCSOARES-1": ShipRoles.CONTRACTOR}
        self.controllers: Dict[str, ShipController] = {
            symbol: ShipController(self.ships[symbol]) for symbol in self.ships}
        self.contract_negotiator = self.ships["SHOCSOARES-2"]

    async def run(self):
        logger.info("MANAGER RUNNING")
        contract = None
        for controller in self.controllers.values():
            asyncio.Task(controller.run())

        while True:
            await asyncio.sleep(0.2)
            if not contract:
                logger.info("No Contract")
                contracts = get_open_contracts()
                if not contracts:
                    logger.info("No open contracts, negotiating")
                    self.contract_negotiator.negotiate_contract()
                    contracts = get_open_contracts()
                contract = contracts[0]
                logger.info(f"New Contract is {contract.id}")
            elif contract.fulfilled:
                logger.info(f"Contract Fulfilled {contract.id}")
                contract = None
            elif not contract.accepted:
                logger.info(f"Accepting {contract.id}, Assigning to SHOCSOARES-1")
                contract.accept()
            elif contract.accepted and (not self.controllers["SHOCSOARES-1"].work_order):
                self.controllers["SHOCSOARES-1"].work_order= FulfillProcurementContract(self.ships["SHOCSOARES-1"], contract)
