

from typing import Set, override
from schemas.market import TradeSymbol
from schemas.ship import Ship
from state_machine.states.ship_state import ShipState


class StateJettison(ShipState):

    def __init__(self, name: str, ship: Ship, keep: Set[TradeSymbol]) -> None:
        self.keep = keep
        super().__init__(name, ship)

    @override
    def do_tick(self) -> bool:
        for item in self.ship.cargo.inventory:
            if item.symbol not in self.keep:
                return self.ship.jettison(item, item.units)
        return False