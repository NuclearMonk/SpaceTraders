from typing import Callable, Optional, Tuple
from schemas.market import TradeGood
from schemas.ship import Ship
from state_machine.states.ship_state import ShipState


class StateDeliverToShip(ShipState):

    def __init__(self, name: str, ship: Ship, get_other_ship: Callable[[], Ship], get_delivery_order: Callable[[], Tuple[TradeGood, int]], callback: Optional[Callable[[int], None]]) -> None:
        super().__init__(name, ship)
        self.get_other_ship = get_other_ship
        self.get_delivery_order = get_delivery_order
        self.callback = callback

    def do_tick(self) -> bool:
        good, units = self.get_delivery_order()
        ship = self.get_other_ship()
        x = self.ship.transfer_cargo(ship, good, units)
        if x and self.callback:
            self.callback(units)
        return x
