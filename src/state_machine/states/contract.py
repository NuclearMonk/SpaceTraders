

from typing import Callable, Optional
from schemas.contract import Contract
from schemas.ship import Ship
from state_machine.states.ship_state import ShipState


class StateNegotiate(ShipState):

    def __init__(self, name: str, ship: Ship, callback: Optional[Callable[[Contract], None]]) -> None:
        super().__init__(name, ship)
        self.callback = callback

    def do_tick(self) -> bool:
        success, contract = self.ship.negotiate_contract()
        if success:
            self.callback(contract)
        return success


class StateAcceptContract(ShipState):

    def __init__(self, name: str, ship: Ship, get_contract: Optional[Callable[[], Contract]]) -> None:
        super().__init__(name, ship)
        self.get_contract = get_contract

    def do_tick(self) -> bool:
        if contract := self.get_contract():
            return contract.accept()
        return False


class StateFulfillContract(ShipState):

    def __init__(self, name: str, ship: Ship, get_contract: Optional[Callable[[], Contract]], set_contract: Optional[Callable[[Optional[Contract]], None]]) -> None:
        super().__init__(name, ship)
        self.get_contract = get_contract
        self.set_contract = set_contract

    def do_tick(self) -> bool:
        if contract := self.get_contract():
            if contract.fulfill():
                self.set_contract(None)
                return True
        return False
