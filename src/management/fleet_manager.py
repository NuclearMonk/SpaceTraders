

from time import sleep
from crud.tradegood import get_good
from management.contract_manager import ContractManager
from management.mining_manager import MiningManager
from management.transport_manager import TransportManager, TransportOrder
from schemas.market import TradeSymbol
from st_requests.ship import get_ship, get_ships
from st_requests.waypoint import get_waypoint


class FleetManager():

    def __init__(self) -> None:
        self.ships = get_ships()
        self.ships_dict = {ship.symbol: ship for ship in self.ships}
        self.transport_manager = TransportManager()
        self.contract_manager = ContractManager(
            self.ships_dict['SHOCSOARES-2'], self.transport_manager)
        self.mining_manager = MiningManager(self.transport_manager)

    def run(self):
        while True:
            sleep(0.5)
            if self.contract_manager.do_cycle():
                continue
            if self.transport_manager.do_cycle():
                continue
            if self.mining_manager.do_cycle():
                continue
