

from typing import Callable, Optional, Set
from management.navigable import Navigable
from schemas.market import TradeGood, TradeSymbol
from schemas.navigation import Waypoint
from schemas.ship import Ship, ShipNavStatus
from state_machine.state_machine import StateMachine, Transition
from state_machine.states.sm_extract import SMExtract
from state_machine.states.sm_travel import SMTravel


class Miner(Navigable):

    def __init__(self, ship: Ship, waypoint: Optional[Waypoint], keep: Set[TradeSymbol], request_pickup: Callable[[Ship, TradeGood, int], None]) -> None:
        super().__init__(ship,waypoint, ShipNavStatus.IN_ORBIT)
        self.assigned_wp = waypoint
        self.state_machine = StateMachine('Miner', [SMTravel('Travel SM', self, False),SMExtract('Extract SM', self.ship, keep,request_pickup)],
                                           [
                                               Transition('Travel SM', 'Extract SM', lambda : self.__at_assigned_waypoint, "In Orbit At Assigned Waypoint"),
                                               Transition( 'Extract SM','Travel SM',  lambda: not self.__at_assigned_waypoint, "In Orbit At Assigned Waypoint")
                                           ],
                                          'Travel SM', root=True)

    def do_tick(self) -> bool:
        return self.state_machine.do_tick()

    @property
    def __at_assigned_waypoint(self)-> bool:
        if self.ship.nav.live_status != ShipNavStatus.IN_ORBIT:
            return False
        if not self.assigned_wp:
            return False
        return self.ship.nav.waypointSymbol == self.assigned_wp.symbol

