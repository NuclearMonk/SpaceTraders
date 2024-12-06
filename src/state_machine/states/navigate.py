
from management.navigable import Navigable
from schemas.ship import ShipNavStatus
from state_machine.states.navigable import NavigableState
from state_machine.states.ship_state import ShipState


class StateNavigate(NavigableState):

    def __init__(self, name: str, navigable: Navigable) -> None:
        super().__init__(name, navigable)

    def on_exit(self) -> bool:
        self.navigable.route.advance()
        return super().on_exit()

    def do_tick(self) -> bool:
        if self.ship.nav.live_status != ShipNavStatus.IN_ORBIT:
            return False
        if not self.navigable.route.current_step.end:
            return False
        return self.ship.navigate(self.navigable.route.current_step.end)