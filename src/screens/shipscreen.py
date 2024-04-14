from textual.app import ComposeResult
from textual.screen import Screen
from textual.reactive import reactive
from textual.widgets import Header, Footer, Label, RichLog
from textual.widgets.data_table import Row
from textual.containers import Vertical, Container
from rich.console import ConsoleRenderable, RichCast
from ship import Ship
from widgets.custom_datatable import CustomDataTable


class ValueLabel(Label):
    """Generates a greeting."""
    label: reactive[str | None] = reactive(None)
    value: reactive[str | None] = reactive(None)

    def __init__(self, label: str, value: str, renderable: ConsoleRenderable | RichCast | str = "", *, expand: bool = False, shrink: bool = False, markup: bool = True, name: str | None = None, id: str | None = None, classes: str | None = None, disabled: bool = False) -> None:
        super().__init__(renderable, expand=expand, shrink=shrink, markup=markup,
                         name=name, id=id, classes=classes, disabled=disabled)
        self.label = label
        self.value = value

    def render(self) -> str:
        return f"{self.label} {self.value}"


class ShipInventoryTable(CustomDataTable):

    def __init__(self, ship: Ship, **kwargs) -> None:
        super().__init__("Inventory", **kwargs)
        self.ship: Ship = ship
        self.add_column("Unit", key="Units", width=6)
        self.add_column("Good", key="Good", width=30)
        self.cursor_type = "row"
        self.styles.height = "100%"
        self.update(self.ship)

    def on_data_table_row_selected(self, row_selected):
        self.ship.sell(row_selected.row_key.value)
    

    def update(self, ship):
        inventory = self.ship.cargo.items()
        to_remove = []
        for rk in self.rows:
            if rk not in inventory:
                to_remove.append(rk)
            else:
                self.update_cell(rk, "Units", inventory[rk])
        for rk in to_remove:
            self.remove_row(rk)
        for rk in inventory:
            if rk not in self.rows:
                self.add_row(inventory[rk], rk, key=rk)

    def on_mount(self):
        self.ship.add_observer(self.update)
        return super().on_mount()

    def on_unmount(self):
        self.ship.remove_observer(self.update)


class ShipScreen(Screen):
    CSS_PATH = "shipscreen.tcss"

    def __init__(self, ship: Ship) -> None:
        self.ship = ship

        self.waypoint = ValueLabel("Waypoint:", self.ship.nav.waypointSymbol)
        self.status = ValueLabel("STATUS:", self.ship.nav.status)
        self.speed = ValueLabel("SPEED:", self.ship.nav.flightMode)
        self.cooldown = ValueLabel("COOLDOWN:", "HH:MM:SS")

        self.destination = ValueLabel(
            "HEADING TO:", self.ship.nav.route.destination.symbol)
        self.destination_coordinates = ValueLabel("COORDINATES:", f"X:{
            self.ship.nav.route.destination.x: <4}Y:{self.ship.nav.route.destination.y: <4}")
        self.eta = ValueLabel("ETA:", "HH:MM:SS")
        self.fuel = ValueLabel(
            "Fuel:", f"{self.ship.fuel.current} / {self.ship.fuel.capacity}")

        self.mounts_table = CustomDataTable(
            "Mounts", id="datatable-mounts", classes="box table", show_header=False)
        self.mounts_table.add_column("Name", key="Name", width=24)
        self.mounts_table.styles.height = "100%"

        self.inventory_table = ShipInventoryTable(self.ship,
                                                  id="datatable-inventory", classes="box table")
        self.inventory_table.border_subtitle = f"{
            self.ship.cargo.units}/{self.ship.cargo.capacity}"

        self.log_panel = RichLog(
            markup=True, wrap=True, classes="box", id="panel-logs")
        self.log_panel.show_vertical_scrollbar = False
        self.log_panel.styles.overflow_x = "hidden"
        self.log_panel.border_title = "Logs"

        super().__init__()

    BINDINGS = [("escape", "app.pop_screen", "Back"),
                ("d", "dock", "Dock"),
                ("o", "orbit", "Orbit"),
                ("s", "survey", "Survey"),
                ("e", "extract", "Extract")]

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="ship-panel", classes="box") as sp:
            sp.border_title = self.ship.symbol
            with Vertical(classes="box") as status:
                status.border_title = "Status"
                yield self.waypoint
                yield self.status
                yield self.speed
                yield self.fuel
                yield self.cooldown
            with Vertical(classes="box") as nav_box:
                nav_box.border_title = "Destination"
                yield self.destination
                yield self.destination_coordinates
                yield self.eta
            yield self.mounts_table
            yield self.inventory_table
            yield self.log_panel

        yield Footer()

    def action_dock(self) -> None:
        self.ship.dock()

    def action_orbit(self) -> None:
        self.ship.orbit()

    def action_survey(self) -> None:
        self.ship.survey()

    def action_extract(self) -> None:
        self.ship.extract()

    def update_logs(self):
        while self.ship.logs:
            self.log_panel.write(self.ship.logs.popleft())

    def update_mounts(self):
        self.mounts_table.clear()
        for mount in self.ship.mounts:
            self.mounts_table.add_row(mount.symbol, key=mount.symbol)

    def update(self, ship):
        self.status.value = self.ship.nav.status
        self.speed.value = self.ship.nav.flightMode
        self.destination.value = self.ship.nav.route.destination.symbol
        self.destination_coordinates.value = f"X:{
            self.ship.nav.route.destination.x: <4}Y:{self.ship.nav.route.destination.y: <4}"
        self.eta.value = self.ship.nav.route.time_remaining
        self.fuel.value = f"{
            self.ship.fuel.current} / {self.ship.fuel.capacity}"
        self.cooldown.value = self.ship.cooldown.time_remaining

        self.update_mounts()
        self.update_logs()

    def tick_seconds(self):
        self.eta.value = str(self.ship.nav.route.time_remaining).split(".")[0]
        self.cooldown.value = str(
            self.ship.cooldown.time_remaining).split(".")[0]

    def on_mount(self) -> None:
        self.update_mounts()
        self.ship.add_observer(self.update)
        self.set_interval(1, self.tick_seconds)

    def on_unmount(self):
        self.ship.remove_observer(self.update)
