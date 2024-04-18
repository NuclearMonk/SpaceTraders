from typing import Dict, List, Type
from textual.app import App, ComposeResult
from textual.driver import Driver
from textual.widgets import Header, Footer
from ai.ship_controller import ShipController
from screens.shiplistscreen import ShipListScreen
from ship import Ship


class SpaceTraders(App):

    BINDINGS = [("d", "toggle_dark", "Toggle Dark Mode")]

    def __init__(self, ships: Dict[str,Ship], ship_controllers: List[ShipController]):
        self.ships = ships
        self.ship_controllers = ship_controllers
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark

    def on_mount(self) -> None:
        for controller in self.ship_controllers:
            self.run_worker(controller.run())
        self.install_screen(ShipListScreen(self.ships), "ship_list")
        self.push_screen("ship_list")
