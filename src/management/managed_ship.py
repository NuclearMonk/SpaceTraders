

class ManagedShip():
    def __init__(self, ship) -> None:
        self.ship=ship
        self.available = True
        self.current_job= None