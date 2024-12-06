from typing import override
from schemas.ship import Ship
from state_machine.state_machine import State


class ShipState(State):

    def __init__(self, name: str, ship: Ship) -> None:
        self.ship = ship
        super().__init__(name)


    def on_enter(self) -> bool:
        self.ship.log(f"ENTERING: {self.name}")
        return super().on_enter()

    def on_exit(self) -> bool:
        self.ship.log(f"EXITING: {self.name}")
        return super().on_exit()
    