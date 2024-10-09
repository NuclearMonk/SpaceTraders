import logging
import pprint
from typing import List
from crud import get_open_contracts
from crud.market import get_market_with_symbol
from crud.waypoint import get_waypoint_with_symbol
from management.managed_ship import ManagedShip
from schemas.contract import Contract
from schemas.navigation import get_system_with_symbol
from schemas.ship import Ship, get_ship_list
logger = logging.getLogger(__name__)


class FleetManager:
    def __init__(self) -> None:
        ships = get_ship_list()
        self.ships = [ManagedShip(ship)for ship in ships]
        # we always have one and it cant do anything else so might as well do this
        self.contract_negotiator = get_ship_with_role(ships, 'SATELLITE')
        # we take it of the general list of ships since it doesn't really make a difference
        self.ships.remove(self.contract_negotiator)
        self.contract = None

    def run(self):
        while True:
            #assumption, it's always profitable to serve a contract, if it's possible
            #so we should always have a contract
            if not self.contract:
                # we fetch from the server, some situations from boot may require it
                contracts = get_open_contracts()
                if not contracts:
                    # then we don't have an open contract at all and should negotiate a new one
                    self.negotiate_new_contract()

                    

    def negotiate_new_contract(self):
        self.contract_negotiator.negotiate_contract()
        
def reload_system_cache(symbol: str)-> None:
    system = get_system_with_symbol(symbol)
    for waypoint in system.waypoints:
        wp = get_waypoint_with_symbol(waypoint.symbol)
        if wp.has_trait("MARKETPLACE"):
            get_market_with_symbol(wp.symbol)


def get_ship_with_role(ships: List[Ship], role: str):
    for s in ships:
        if s.registration.role == role:
            return s
    else:
        return None
