from textual.app import App, ComposeResult
from textual.widgets import Header, Footer

from screens.shiplistscreen import ShipListScreen


class SpaceTraders(App):

    BINDINGS = [("d", "toggle_dark", "Toggle Dark Mode")]
    SCREENS = {"ship_list": ShipListScreen()}

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark

    def on_mount(self) -> None:
        self.push_screen("ship_list")
