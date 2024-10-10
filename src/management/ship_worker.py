

import asyncio
from typing import Optional
from management.jobs.job import Job
from schemas.ship import Ship


class Worker:

    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.symbol = ship.symbol
        self.idle: bool = True
        self.job: Optional[Job] = None

    def assign_job(self, job:Job):
        self.idle= False
        self.job = job

    async def run(self):
        while True:
            await asyncio.sleep(0.2)
            if self.job:
                self.idle = False
                self.ship.log("CONTROLLER: Has Work Order")
                if not await self.job.execute():
                    self.ship.logger("CONTROLLER: EXECUTION FAILED")
                self.job = None
                self.idle = True
