

import asyncio
from enum import StrEnum
from typing import Dict
from ai.ship_controller import ShipController
from management.work_orders.work_order import FulfillProcurementContract
from schemas.contract import get_open_contracts
from schemas.ship import Ship, get_ship_list



class ShipRoles(StrEnum):
    CONTRACTOR = "Contractor"



class FleetManager():
    def __init__(self) -> None:
        print("STARTING MANAGER")
        self.ships : Dict[str, Ship]= {ship.symbol: ship for ship in get_ship_list()}
        self.roles = {"SHOCSOARESS-1": ShipRoles.CONTRACTOR}
        self.controllers : Dict[str, ShipController]= {symbol: ShipController(self.ships[symbol]) for symbol in self.ships}


    async def run(self):
        print("Running")
        contract = None
        for controller in self.controllers.values():
            asyncio.Task(controller.run())
            
        while True:
            await asyncio.sleep(0.2)
            if not contract:
                print("No Contract")
                contracts = get_open_contracts()
                if not contracts:
                    print("No open contracts, negotiating")
                    self.ships["SHOCSOARESS-2"].negotiate_contract()
                    contracts = get_open_contracts()
                contract = contracts[0]
                print(f"New Contract is {contract.id}")
            if contract.fulfilled:
                print(f"Contract Fulfilled {contract.id}")
                contract = None
            if not contract.accepted:
                print(f"Accepting {contract.id}, Assigning to SHOCSOARESS-1")
                contract.accept()
            if contract.accepted and (not self.controllers["SHOCSOARESS-1"].work_order):
                print("WTF")
                self.controllers["SHOCSOARESS-1"].work_order= FulfillProcurementContract(self.ships["SHOCSOARESS-1"], contract)
