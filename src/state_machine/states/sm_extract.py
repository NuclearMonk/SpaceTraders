from typing import Callable, Set
from schemas.market import TradeGood, TradeSymbol
from schemas.ship import Ship
from state_machine.state_machine import StateMachine, Transition
from state_machine.states.await_pickup import StateAwaitPickup
from state_machine.states.extract import StateExtract
from state_machine.states.jettison import StateJettison
from state_machine.states.waiting import StateWaiting


class SMExtract(StateMachine):

    def __init__(self,name: str, ship: Ship, keep: Set[TradeSymbol], request_pickup: Callable[[Ship, TradeGood, int], None]) -> None:
        self.ship = ship
        self.keep = keep
        self.request_pickup = lambda good, units: request_pickup(self.ship, good, units)
        super().__init__(name, [StateWaiting('Awaiting Cooldown', ship),
                                        StateAwaitPickup('Awaiting Pickup', ship, self.request_pickup),
                                        StateExtract('Extract', ship),
                                        StateJettison('Jettison', ship, self.keep)],
                         [
            Transition('Awaiting Cooldown', 'Extract',
                       lambda: not self.__on_cooldown, "Cooldown = 0"),
            Transition('Awaiting Cooldown', 'Jettison',
                       lambda: self.__has_useless_cargo, "Has Useless Cargo"),
            Transition('Extract', 'Jettison',
                       lambda: self.__has_useless_cargo, "Has Useless Cargo"),
            Transition('Extract', 'Awaiting Pickup',
                       lambda: self.__cargo_full and not self.__has_useless_cargo, "Cargo Full"),
            Transition('Extract', 'Awaiting Cooldown',
                       lambda: self.__on_cooldown, "Cooldown != 0"),
            Transition('Jettison', 'Awaiting Cooldown',
                       lambda:  self.__on_cooldown and not self.__has_useless_cargo, "No Useless Cargo"),
            Transition('Jettison', 'Extract',
                       lambda: not self.__has_useless_cargo and not self.__on_cooldown, "No Useless Cargo, Cooldown == 0"),
            Transition('Awaiting Pickup', 'Awaiting Cooldown',
                       lambda: not self.__cargo_full, "Cargo Not Full")
        ], 'Awaiting Cooldown')


    def on_enter(self):
        self.ship.log(f"ENTERING:{self.name}")
        return super().on_enter()

    def on_exit(self):
        self.ship.log(f"EXITING:{self.name}")
        return super().on_exit()

    @property
    def __on_cooldown(self) -> bool:
        return self.ship.cooldown.time_remaining.total_seconds() != 0

    @property
    def __has_useless_cargo(self) -> bool:
        for item in self.ship.cargo.inventory:
            if item.symbol not in self.keep:
                return True
        return False
    @property
    def __cargo_full(self) -> bool:
        return self.ship.cargo.capacity_remaining == 0
