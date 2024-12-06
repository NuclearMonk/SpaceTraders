

from typing import override
from schemas.ship import Ship
from state_machine.state_machine import State
from state_machine.states.ship_state import ShipState


class StateExtract(ShipState):

    def __init__(self, name: str, ship: Ship) -> None:
        super().__init__(name, ship)
        self.survey = None

    def on_enter(self) -> bool:
        # TODO add get survey logic
        return super().on_enter()

    def on_exit(self) -> bool:
        self.survey = None
        return super().on_exit()

    @override
    def do_tick(self) -> bool:
        if self.survey:
            return self.ship.extract_with_survey(self.survey)
        return self.ship.extract()
