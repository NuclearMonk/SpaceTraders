

from schemas.ship import Ship
from state_machine.states.ship_state import ShipState


class StateRefuel(ShipState):

    def __init__(self, name: str, ship: Ship) -> None:
        super().__init__(name, ship)

    def do_tick(self) -> bool:
        return self.ship.refuel()