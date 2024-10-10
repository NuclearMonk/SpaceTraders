

from schemas.ship import Ship


class Job:
    
    def start(self,ship: Ship):
        return True

    async def work(self,ship: Ship):
        return True

    def end(self,ship: Ship):
        return True    

    async def execute(self,ship: Ship):
        if not self.start(ship):
            return False
        if not await self.work(ship):
            return False
        if not self.end(ship):
            return False
        return True