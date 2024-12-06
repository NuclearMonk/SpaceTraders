from typing import Callable, Optional, Set, override
from management.transport_order import TransportOrder
from schemas import contract
from schemas.contract import Contract
from schemas.market import TradeGood, TradeSymbol
from schemas.ship import Ship
from st_requests.contract import get_all_contracts_from_server, get_open_contracts
from st_requests.market import get_markets_exporting
from state_machine.state_machine import StateMachine, Transition
from state_machine.states.await_pickup import StateAwaitPickup
from state_machine.states.extract import StateExtract
from state_machine.states.jettison import StateJettison
from state_machine.states.contract import StateAcceptContract, StateFulfillContract, StateNegotiate
from state_machine.states.ship_state import ShipState
from state_machine.states.waiting import StateWaiting
from utils.utils import utcnow


class StateAwaitDeliveries(StateWaiting):

    def __init__(self, name: str, ship: Ship, get_contract: Optional[Callable[[], Contract]], request_pickup: Callable[[TransportOrder], None]) -> None:
        super().__init__(name, ship)
        self.get_contract = get_contract
        self.request_pickup = request_pickup

    def on_enter(self) -> bool:
        if not (contract := self.get_contract()):
            return False
        self.request_pickup(contract)
        return True


class SMNegotiate(StateMachine):

    def __init__(self, name: str, ship: Ship, request_pickup: Callable[[Contract], None], get_contract: Optional[Callable[[], Optional[Contract]]], set_contract: Optional[Callable[[Optional[Contract]], None]], root= False) -> None:
        self.ship = ship
        self.request_pickup = request_pickup
        self.get_contract = get_contract
        self.set_contract = set_contract

        super().__init__(name,
                         [StateWaiting('Entry', ship),
                          StateNegotiate('Negotiate', ship, self.set_contract),
                          StateWaiting('Impossible Contract',ship),
                          StateAcceptContract(
                              'Accept', ship, self.get_contract),
                          StateAwaitDeliveries(
                              'Awaiting Deliveries', ship, self.get_contract, self.request_pickup),
                          StateFulfillContract('Fulfill', ship, self.get_contract, self.set_contract)],
                         [
                             Transition('Entry', 'Negotiate',
                                        lambda: not self.get_contract(),"No Contract"),
                             Transition('Entry', 'Impossible Contract',
                                        lambda: not self.__is_contract_possible,"Impossible Contract"),
                             Transition('Entry', 'Accept',
                                        lambda: self.__is_contract_possible and not self.get_contract().accepted, "Contract Possible and Not Accepted"),
                             Transition('Entry', 'Awaiting Deliveries',
                                        lambda: self.__is_contract_possible and  self.get_contract().accepted and not self.get_contract().ready_to_fulfill, "Contract Accepted Not Ready To Fullfill"),
                             Transition('Entry', 'Fulfill',
                                        lambda: self.__is_contract_possible and  self.get_contract().accepted and self.get_contract().ready_to_fulfill, "Contract Ready To Fullfill"),
                             Transition('Negotiate', 'Impossible Contract',
                                        lambda: not self.__is_contract_possible, "Impossible Contract"),
                             Transition('Negotiate', 'Accept',
                                        lambda: self.__is_contract_possible and not self.get_contract().accepted, "Possible and Not Accepted"),
                             Transition('Impossible Contract', 'Negotiate',
                                        lambda: self.__deadline_to_accept_expired, "Expired"),
                             Transition('Accept', 'Awaiting Deliveries',
                                        lambda: self.get_contract() and self.get_contract().accepted and not self.get_contract().ready_to_fulfill,"Contract Open"),
                             Transition('Accept', 'Fulfill',
                                        lambda: self.get_contract() and self.get_contract().ready_to_fulfill, "Ready to Fulfill"),
                             Transition('Awaiting Deliveries', 'Fulfill',
                                        lambda: self.get_contract() and self.get_contract().ready_to_fulfill, "Ready to Fulfill"),
                             Transition('Fulfill', 'Negotiate',
                                        lambda: not self.get_contract(),"No Contract"),
                         ],
                         'Entry', root)

    def on_enter(self) -> bool:
        self.ship.log(f"ENTERING:{self.name}")
        return super().on_enter()

    def on_exit(self) -> bool:
        self.ship.log(f"EXITING:{self.name}")
        return super().on_exit()

    @property
    def __deadline_to_accept_expired(self):
        if not self.get_contract():
            return True
        return self.get_contract().deadlineToAccept < utcnow()

    @property
    def __is_contract_possible(self) -> bool:
        if not self.get_contract():
            return False
        for delivery in self.get_contract().terms.deliver:
            if not get_markets_exporting(delivery.tradeSymbol):
                return False
        return True
