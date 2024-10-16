

import asyncio
from typing import Optional
from management.routines.routine import Routine
from schemas.ship import Ship


class ShipWorker:

    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.symbol = ship.symbol
        self.idle: bool = True
        self.job: Optional[Routine] = None

    def assign_routine(self, job:Routine):
        self.idle= False
        self.job = job

    async def run(self):
        while True:
            await asyncio.sleep(0.2)
            if self.job:
                self.idle = False
                self.ship.log("Worker: Has Work Order")
                if not await self.job.execute(self.ship):
                    self.ship.logger("Worker: EXECUTION FAILED")
                self.job = None
                self.idle = True
