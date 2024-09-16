

import asyncio
from datetime import UTC, datetime
from schemas.ship import Ship
from utils.utils import console, format_time_ms
from asyncio import create_task


class ShipController():
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.busy = False
        self.ship.logger = self.ship.logger
        self.work_order = None

    async def run(self):
        self.ship.logger(f"{self.ship.symbol} CONTROLLER"
                         + "@{format_time_ms(datetime.now(UTC))}] Controller Running")
        while True:
            await asyncio.sleep(0.2)
            if self.work_order:
                self.busy = True
                self.ship.logger(f"{self.ship.symbol} CONTROLLER"
                         + "@{format_time_ms(datetime.now(UTC))}] Has Work Order")
                if not await self.work_order.execute():
                    self.ship.logger(f"{self.ship.symbol} CONTROLLER"
                         + "@{format_time_ms(datetime.now(UTC))}] EXECUTION FAILED")
                self.work_order = None
                self.busy = False
