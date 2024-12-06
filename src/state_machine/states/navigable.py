


from management.navigable import Navigable
from state_machine.states.ship_state import ShipState


class NavigableState(ShipState):

    def __init__(self, name: str, navigable: Navigable) -> None:
        self.navigable = navigable
        super().__init__(name, self.navigable.ship)