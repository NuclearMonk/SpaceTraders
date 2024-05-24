

import asyncio
from schemas.ship import Ship
from utils.utils import console
from asyncio import create_task

class ShipController():
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.busy = False
        self.ship.logger = console.print
        self.work_order = None


    async def run(self):
        print(f"running worker {self.ship.symbol}")
        while True:
            await asyncio.sleep(0.2)
            if self.work_order:
                self.busy = True
                print(f"{self.ship.symbol}Has Work Order")
                if not await self.work_order.execute():
                    print("EXECUTION FAILED")
                self.work_order = None
                self.busy = False