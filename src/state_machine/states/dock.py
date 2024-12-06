from schemas.ship import Ship, ShipNavStatus
from state_machine.states.ship_state import ShipState


class StateDock(ShipState):


    def __init__(self, name: str, ship: Ship) -> None:
        super().__init__(name, ship)

    def do_tick(self) -> bool:
        if self.ship.nav.live_status != ShipNavStatus.IN_ORBIT:
            return False
        return self.ship.dock()