

from schemas.ship import Ship


class Job:
    

    def __init__(self, ship: Ship) -> None:
        self.ship = ship

    def start(self):
        return True

    async def work(self):
        return True

    def end(self):
        return True    

    async def execute(self):
        if not self.start():
            return False
        if not await self.work():
            return False
        if not self.end():
            return False
        return True