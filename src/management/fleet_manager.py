import asyncio
import collections
import logging
import pprint
from typing import List
from crud import get_open_contracts
from crud.contract import refresh_contract_cache
from crud.market import get_market_with_symbol, get_markets_importing
from crud.waypoint import get_waypoint_with_symbol, get_waypoints_in_system, refresh_system_cache
from management.jobs.job import Job
from management.jobs.mine import Mine
from management.jobs.sell import Sell
from management.jobs.travel import Travel
from management.ship_worker import Worker
from schemas.contract import Contract
from schemas.ship import Ship, get_ship_list
logger = logging.getLogger(__name__)


class FleetManager:
    def __init__(self) -> None:
        ships = get_ship_list()
        self.contract_negotiator = get_ship_with_role(ships, 'SATELLITE')
        ships.remove(self.contract_negotiator)
        self.ships = ships
        self.workers= [Worker(ship) for ship in self.ships]

        # we always have one and it cant do anything else so might as well do this
        # we take it of the general list of ships since it doesn't really make a difference
        self.contract = None
        self.update_caches()

    def run(self):
        while True:
            asyncio.sleep(1)
            for worker in self.workers:
                print(worker.symbol, worker.idle)
                if not worker.idle:
                    continue
                worker.assign_job(find_best_job(worker))
                break
            
                    
    
    def systems_with_ships(self):
        systems = {ship.nav.systemSymbol for ship in self.ships}
        systems.add(self.contract_negotiator.nav.systemSymbol)
        return list(systems)
    
    def update_caches(self):
        refresh_contract_cache()
        for system in self.systems_with_ships():
            refresh_system_cache(system)

    def negotiate_new_contract(self):
        self.contract_negotiator.negotiate_contract()
        


def find_best_job(worker:Worker)-> Job:
    good_symbols = ["ALUMINUM_ORE", "COPPER_ORE", "IRON_ORE"]
    if worker.ship.cargo.capacity_remaining == 0:
        if worker.ship.nav.waypointSymbol != "X1-DV3-H49":
            return Travel(get_waypoint_with_symbol("X1-DV3-H49"))
        goods_in_ship = {s for s,_  in worker.ship.cargo.items}
        return Sell(list(goods_in_ship.intersection(good_symbols)))
    if worker.ship.nav.waypointSymbol != "X1-DV3-XZ5D":
        return Travel(get_market_with_symbol("X1-DV3-XZ5D"))
    return Mine(list(good_symbols))

def get_ship_with_role(ships: List[Ship], role: str):
    for s in ships:
        if s.registration.role == role:
            return s
    else:
        return None
