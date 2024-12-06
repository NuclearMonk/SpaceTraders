from schemas.ship import Ship, ShipNavFlightMode
from state_machine.states.ship_state import ShipState


class StateDrift(ShipState):

    def __init__(self, name: str, ship: Ship) -> None:
        super().__init__(name, ship)

    def do_tick(self) -> bool:
        print(self.ship.nav.flightMode)
        if self.ship.nav.flightMode == ShipNavFlightMode.DRIFT:
            print("WTF DRIFT")
            return False
        return self.ship.change_flight_mode(ShipNavFlightMode.DRIFT)

class StateCruise(ShipState):

    def __init__(self, name: str, ship: Ship) -> None:
        super().__init__(name, ship)

    def do_tick(self) -> bool:
        print(self.ship.nav.flightMode)

        if self.ship.nav.flightMode == ShipNavFlightMode.CRUISE:
            print("WTF CRUISE")
            return False
        return self.ship.change_flight_mode(ShipNavFlightMode.CRUISE)