from typing import Callable, Optional, Tuple
from schemas.market import TradeGood
from schemas.ship import Ship
from st_requests.market import get_market
from state_machine.states.ship_state import ShipState


class StatePurchase(ShipState):

    def __init__(self, name: str, ship: Ship, get_purchase_order: Callable[[], Tuple[TradeGood, int]], callback: Optional[Callable[[int], None]]) -> None:
        super().__init__(name, ship)
        self.get_purchase_order = get_purchase_order
        self.callback = callback

    def do_tick(self) -> bool:
        good, units = self.get_purchase_order()
        market = get_market(self.ship.nav.route.destination.symbol)
        units = min(units,market.trade_good_trade_volume(good))
        x = self.ship.purchase(good, units)
        if x and self.callback:
            self.callback(units)
        return x
