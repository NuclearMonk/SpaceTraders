

from typing import Callable, Optional
from crud.tradegood import get_good
from management.transport_order import TransportOrder
from schemas.contract import Contract
from schemas.ship import Ship
from state_machine.states.sm_negotiator import SMNegotiate


class Negotiator:

    def __init__(self, ship: Ship,
                 request_pickup: Callable[[Contract], None],
                 get_contract: Optional[Callable[[], Optional[Contract]]],
                 set_contract: Optional[Callable[[Optional[Contract]], None]]) -> None:
        self.ship = ship
        self.state_machine = SMNegotiate('Negotiate SM',self.ship,request_pickup, get_contract,set_contract, root=True)

    def do_tick(self):
        return self.state_machine.do_tick()


