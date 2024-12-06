

from typing import Callable, Optional, Tuple
from schemas.market import TradeGood
from schemas.ship import Ship
from state_machine.states.ship_state import ShipState


class StatePickupFromShip(ShipState):

    def __init__(self, name: str, ship: Ship, get_other_ship: Callable[[], Ship], get_pickup_order: Callable[[], Tuple[TradeGood, int]], callback: Optional[Callable[[int], None]]) -> None:
        super().__init__(name, ship)
        self.get_other_ship = get_other_ship
        self.get_pickup_order = get_pickup_order
        self.callback = callback

    def do_tick(self) -> bool:
        good, units = self.get_pickup_order()
        ship = self.get_other_ship()
        x = ship.transfer_cargo(self.ship, good, units)
        if x and self.callback:
            self.callback(units)
        return x
