from dataclasses import dataclass
from typing import Optional
from schemas.contract import Contract
from schemas.market import TradeGood
from schemas.navigation import Waypoint
from schemas.ship import Ship


@dataclass
class TransportOrder:
    good: TradeGood
    units_total: int
    pickup_wp: Waypoint
    delivery_wp: Waypoint
    units_picked_up: int = 0
    units_delivered: int = 0
    units_assigned: int = 0
    pickup_ship: Optional[Ship] = None
    delivery_ship: Optional[Ship] = None
    contract: Optional[Contract] = None

    def __str__(self) -> str:
        return f"{self.pickup_wp.symbol}({self.pickup_ship.symbol if self.pickup_ship else ""})->{self.delivery_wp.symbol}({self.delivery_ship.symbol if self.delivery_ship else ""}) {self.good.symbol} {self.units_picked_up}/{self.units_delivered}/{self.units_total}"