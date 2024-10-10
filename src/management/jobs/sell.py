from typing import List
from management.jobs.job import Job
from schemas.ship import Ship


class Sell(Job):

    def __init__(self, sell: List[str]) -> None:
        self.sell = sell


    def start(self,ship: Ship):
        ship.log("Sell: Job Started")
        self.docked = ship.nav.status == "DOCKED"
        if not self.docked:
            ship.log("Sell: Docking")
            ship.dock()
        return True

    async def work(self, ship: Ship):
        for good_symbol in self.sell:
            ship.log(f"Sell: Selling {good_symbol}")
            if not ship.sell(good_symbol):
                return False
        return True

    def end(self, ship: Ship):
        if not self.docked:
            ship.log("Sell: Orbit")
            ship.orbit()
        ship.log("Sell: Done")
        return True