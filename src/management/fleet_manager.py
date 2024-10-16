import asyncio
import logging
from typing import List
from crud.contract import refresh_contract_cache
from crud.market import get_market_with_symbol
from crud.waypoint import get_waypoint_with_symbol, refresh_system_cache
from management.routines.routine import Routine
from management.routines.mine import Mine
from management.routines.sell import Sell
from management.routines.travel import Travel
from management.ship_worker import ShipWorker
from schemas.ship import Ship, get_ship_list
logger = logging.getLogger(__name__)


class FleetManager:
    def __init__(self) -> None:
        ships = get_ship_list()
        self.contract_negotiator = get_ship_with_role(ships, 'SATELLITE')
        ships.remove(self.contract_negotiator)
        self.ships = ships
        self.workers= [ShipWorker(ship) for ship in self.ships]

        # we always have one and it cant do anything else so might as well do this
        # we take it of the general list of ships since it doesn't really make a difference
        self.contract = None
        self.update_caches()

    async def run(self):
        for worker in self.workers:
            asyncio.Task(worker.run())
        while True:
            await asyncio.sleep(1)
            for worker in self.workers:
                if not worker.idle:
                    continue
                worker.assign_routine(find_best_job(worker))
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
        


def find_best_job(worker:ShipWorker)-> Routine:
    good_symbols = ["ALUMINUM_ORE", "COPPER_ORE", "IRON_ORE"]
    if worker.ship.cargo.capacity_remaining == 0:
        if worker.ship.nav.waypointSymbol != "X1-DV3-H49":
            return Travel(get_waypoint_with_symbol("X1-DV3-H49"))
        goods_in_ship = {s for s  in worker.ship.cargo.items()}
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
