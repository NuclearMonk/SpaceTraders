
from typing import Dict, List
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from management.fleet_manager import FleetManager
from schemas.ship import Ship
from ui.screens.ship_list_screen import ShipListScreen


class SpaceTraders(App):

    BINDINGS = [("d", "toggle_dark", "Toggle Dark Mode")]

    def __init__(self):
        self.fleet_manager = FleetManager()
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark

    def on_mount(self) -> None:
        self.run_worker(self.fleet_manager.run())
        self.install_screen(ShipListScreen(self.fleet_manager.ships_dict), "ship_list")
        self.push_screen("ship_list")