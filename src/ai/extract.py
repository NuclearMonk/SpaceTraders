from asyncio import sleep
import math
from ship import Ship


async def extract_loop(ship: Ship)->None:
    while ship.cargo.units < ship.cargo.capacity:
        await sleep(math.ceil(ship.cooldown.time_remaining.total_seconds()))
        ship.extract()