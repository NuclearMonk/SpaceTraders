from asyncio import run
import asyncio
from typing import Dict
from ai.mining_procurement_ship import ProcurementMinerController
from ai.mining_ship import MinerShipController
from schemas.contract import get_contract
from schemas.ship import Ship, get_ship_list
from ui.ui import SpaceTraders


ui = False
if __name__ == "__main__":
    ships: Dict[str, Ship] = {ship.symbol: ship for ship in get_ship_list()}
    ship_controllers = [MinerShipController(
        ships["SHOCSOARES-1"], "X1-U25-DX5C", "X1-U25-H52", ["ALUMINUM_ORE", "COPPER_ORE", "IRON_ORE"])]
    if ui:
        app = SpaceTraders(ships, ship_controllers)
        app.run()
    else:
        for controller in ship_controllers:
            asyncio.run(controller.run())
