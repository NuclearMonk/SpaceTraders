

from schemas.ship import Ship


class ManagedShip():
    def __init__(self, ship) -> None:
        self.ship: Ship=ship
        self.available = True
        self.current_job= None