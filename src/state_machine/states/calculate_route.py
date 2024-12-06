

from typing import Callable, Optional, Tuple, override
from management.navigable import Navigable
from pathfinding.pathfinding import calculate_route
from schemas.navigation import Waypoint
from schemas.ship import ShipNavStatus
from state_machine.states.navigable import NavigableState


class StateCalculatingRoute(NavigableState):

    def __init__(self, name: str, navigable: Navigable, get_destination: Callable[[], Optional[Tuple[Waypoint, ShipNavStatus]]]) -> None:
        super().__init__(name, navigable)
        self.get_destination = get_destination

    @override
    def do_tick(self) -> bool:
        if x := self.get_destination():
            destination, status = x
            self.navigable.set_destination(destination,status)
        return False
