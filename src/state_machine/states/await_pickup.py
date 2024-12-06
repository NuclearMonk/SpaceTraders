

from typing import Callable
from schemas.market import TradeGood
from schemas.ship import Ship
from state_machine.states.waiting import StateWaiting


class StateAwaitPickup(StateWaiting):

    def __init__(self, name: str, ship: Ship, request_pickup: Callable[[TradeGood, int],None]) -> None:
        super().__init__(name, ship)
        self.request_pickup = request_pickup

    def on_enter(self) -> bool:
        for item in self.ship.cargo.inventory:
            self.request_pickup(item, item.units)
        return super().on_enter()