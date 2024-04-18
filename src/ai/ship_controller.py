

from ship import Ship
from utils import console


class ShipController():
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.ship.logger = console.print

    async def run():
        ...