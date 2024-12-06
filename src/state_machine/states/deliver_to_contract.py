from typing import Callable, Optional, Tuple
from schemas.contract import Contract
from schemas.market import TradeGood
from schemas.ship import Ship
from state_machine.states.ship_state import ShipState


class StateDeliverToContract(ShipState):

    def __init__(self, name: str, ship: Ship, get_contract: Callable[[], Contract], get_delivery_order: Callable[[], Tuple[TradeGood, int]], callback: Optional[Callable[[int], None]]) -> None:
        super().__init__(name, ship)
        self.get_contract = get_contract
        self.get_delivery_order = get_delivery_order
        self.callback = callback

    def do_tick(self) -> bool:
        good, units = self.get_delivery_order()
        contract = self.get_contract()
        x = self.ship.deliver_to_contract(contract, good, units)
        if x and self.callback:
            self.callback(units)
        return x
