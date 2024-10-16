


import asyncio
from management.routines.routine import Routine
from schemas.ship import Ship


class WaitForArrival(Routine):


    async def work(self, ship: Ship):
        return await asyncio.sleep(ship.nav.route.time_remaining.total_seconds)
