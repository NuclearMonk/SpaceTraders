

from typing import List
from management.navigable import Navigable
from schemas.ship import ShipNavFlightMode, ShipNavStatus
from state_machine.state_machine import State, StateMachine, Transition
from state_machine.states.dock import StateDock
from state_machine.states.orbit import StateOrbit
from state_machine.states.refuel import StateRefuel
from state_machine.states.waiting import StateWaiting
from state_machine.states.speed import StateCruise, StateDrift
from state_machine.states.navigate import StateNavigate


class SMTravel(StateMachine):

    def __init__(self, name, navigable: Navigable, root=False) -> None:
        self.navigable = navigable
        super().__init__(name,
                         [StateWaiting('In Transit', self.navigable.ship),
                          StateWaiting('Done', self.navigable.ship),
                          StateWaiting('Docked', self.navigable.ship),
                          StateWaiting('In Orbit', self.navigable.ship),
                          StateDock('Dock', self.navigable.ship),
                          StateRefuel('Refuel', self.navigable.ship),
                          StateOrbit('Orbit', self.navigable.ship),
                          StateCruise('Set Cruise', self.navigable.ship),
                          StateDrift('Set Drift', self.navigable.ship),
                          StateNavigate('Navigate', self.navigable)],
                         [
                             Transition(
                                 'In Transit', 'In Orbit', lambda: self.navigable.ship.nav.live_status == ShipNavStatus.IN_ORBIT, "In Orbit"),
                             Transition(
                                 'In Transit', 'Docked', lambda: self.navigable.ship.nav.live_status == ShipNavStatus.DOCKED, "Docked"),
                             Transition(
                                 'Orbit', 'In Orbit', lambda: self.navigable.ship.nav.live_status == ShipNavStatus.IN_ORBIT, "In Orbit"),
                             Transition(
                                 'Dock', 'Docked', lambda: self.navigable.ship.nav.live_status == ShipNavStatus.DOCKED, "Docked"),
                             Transition('In Orbit', 'Done', lambda: self.__at_destination and (
                                 self.navigable.destination_status == ShipNavStatus.IN_ORBIT), "Orbiting at Orbit Destination"),
                             Transition('Docked', 'Done', lambda: self.__at_destination and (
                                 self.navigable.ship.nav.live_status == ShipNavStatus.DOCKED), "Docked At Docked Destination"),
                             Transition(
                                 'Docked', 'Refuel', lambda: not self.__fuel_full and self.__needs_refuel, "Needs Fuel"),
                             Transition(
                                 'Docked', 'Orbit', lambda: not self.__needs_refuel or self.__fuel_full, "No Need to Fuel"),
                             Transition('Docked', 'Orbit', lambda: not self.__at_destination and (
                                 self.navigable.destination_status == ShipNavStatus.IN_ORBIT), "Docked at a Orbit Destination"),
                             Transition(
                                 'Refuel', 'Docked', lambda: self.__fuel_full, "Fuel is Full"),
                             Transition('In Orbit', 'Dock', lambda: self.__at_destination and (
                                 self.navigable.destination_status == ShipNavStatus.DOCKED), "Orbiting at a Docked Destination"),
                             Transition(
                                 'In Orbit', 'Dock', lambda: not self.__fuel_full and self.__needs_refuel, "Needs To Refuel"),
                             Transition(
                                 'In Orbit', 'Set Cruise', lambda: self.__needs_set_cruise, "Needs Cruise"),
                             Transition(
                                 'In Orbit', 'Set Drift', lambda: self.__needs_set_drift, "Needs Drift"),
                             Transition(
                                 'In Orbit', 'Navigate', lambda: self.__ready_to_navigate, "Ready To Navigate"),
                             Transition('Set Cruise', 'In Orbit', lambda: self.navigable.ship.nav.flightMode ==
                                        ShipNavFlightMode.CRUISE, "In Cruise"),
                             Transition(
                                 'Set Drift', 'In Orbit', lambda: self.navigable.ship.nav.flightMode == ShipNavFlightMode.DRIFT, "In Drift"),
                             Transition(
                                 'Navigate', 'In Transit', lambda: not self.__has_arrived, "In Transit")
                         ], 'In Transit', root)

    def on_enter(self):
        self.navigable.ship.log(f"ENTERING:{self.name}")
        return super().on_enter()

    def on_exit(self):
        self.navigable.ship.log(f"EXITING:{self.name}")
        return super().on_exit()

    @property
    def __has_arrived(self) -> bool:
        return self.navigable.ship.nav.live_status != ShipNavStatus.IN_TRANSIT

    @property
    def __at_destination(self) -> bool:
        return self.__has_arrived and (self.navigable.destination.symbol == self.navigable.ship.nav.waypointSymbol)

    @property
    def __needs_refuel(self) -> bool:
        if self.navigable.route.current_step:
            return self.navigable.route.current_step.refuel
        return False

    @property
    def __fuel_full(self) -> bool:
        return self.navigable.ship.fuel.current == self.navigable.ship.fuel.capacity

    @property
    def __needs_set_drift(self) -> bool:
        if self.navigable.route.current_step:
            if self.navigable.route.current_step.flight_mode == ShipNavFlightMode.DRIFT:
                return self.navigable.ship.nav.flightMode != ShipNavFlightMode.DRIFT
        return False

    @property
    def __needs_set_cruise(self) -> bool:
        if self.navigable.route.current_step:
            if self.navigable.route.current_step.flight_mode == ShipNavFlightMode.CRUISE:
                return self.navigable.ship.nav.flightMode != ShipNavFlightMode.CRUISE
        return False

    @property
    def __ready_to_navigate(self):
        return self.navigable.route.current_step.flight_mode == self.navigable.ship.nav.flightMode
