from typing import Dict
from textual.app import ComposeResult
from textual.widgets import DataTable
from textual.screen import Screen
from screens.shipscreen import ShipScreen
from ship import Ship, get_ship_table
from utils import format_time_ms


class ShipListScreen(Screen):
    CSS_PATH = None
    ships: Dict[str, Ship] = get_ship_table()

    def compose(self) -> ComposeResult:     
        yield DataTable(zebra_stripes=True)  

    def tick_seconds(self):
        for ship_id, ship in self.ships.items():
            self.ship_table.update_cell(
                ship_id, "ETA", ship.nav.route.time_remaining)
            self.ship_table.update_cell(
                ship_id, "Cooldown", ship.cooldown.time_remaining)

    def on_mount(self) -> None:

        self.ship_table = self.query_one(DataTable)
        columns = ["Symbol", "Waypoint", "Status", "Mode", "Destination",
                   "Arrival Time", "ETA", "Cooldown", "Fuel", "Max", "Cargo", "Cap"]
        self.ship_table.cursor_type = "row"
        for c in columns:
            self.ship_table.add_column(c, key=c)
        for name, ship in self.ships.items():
            self.ship_table.add_row(ship.symbol,
                                    ship.nav.waypointSymbol,
                                    ship.nav.status,
                                    ship.nav.flightMode,
                                    ship.nav.route.destination.symbol,
                                    format_time_ms(ship.nav.route.arrival),
                                    "HH:MM:SS.FFF",
                                    ship.cooldown.remainingSeconds,
                                    ship.fuel.current,
                                    ship.fuel.capacity, ship.cargo.units,
                                    ship.cargo.capacity,
                                    key=name)

        self.set_interval(1, self.tick_seconds)
        for symbol, ship in self.ships.items():
            ship.add_observer(self.update_row)

    def update_row(self, ship: Ship):
        self.ship_table.update_cell(
            ship.symbol, "Waypoint", ship.nav.waypointSymbol)
        self.ship_table.update_cell(ship.symbol, "Status", ship.nav.status)
        self.ship_table.update_cell(ship.symbol, "Mode", ship.nav.flightMode)
        self.ship_table.update_cell(
            ship.symbol, "Mode", ship.nav.route.destination.symbol)
        self.ship_table.update_cell(
            ship.symbol, "Arrival Time", format_time_ms(ship.nav.route.arrival))
        self.ship_table.update_cell(
            ship.symbol, "ETA", ship.nav.route.time_remaining)
        self.ship_table.update_cell(
            ship.symbol, "Cooldown", ship.cooldown.time_remaining)
        self.ship_table.update_cell(ship.symbol, "Fuel", ship.fuel.current)
        self.ship_table.update_cell(ship.symbol, "Max", ship.fuel.capacity)
        self.ship_table.update_cell(ship.symbol, "Cargo", ship.cargo.units)
        self.ship_table.update_cell(ship.symbol, "Cap", ship.fuel.capacity)

    def on_data_table_row_selected(self, row_selected):
        self.app.push_screen(ShipScreen(
            self.ships[row_selected.row_key.value]))
