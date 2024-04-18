from asyncio import run
from typing import Dict
from ai.mining_ship import MinerShipController
from ship import Ship, get_ship_list
from ui import SpaceTraders


if __name__ == "__main__":
    ships: Dict[str, Ship] = {ship.symbol: ship for ship in get_ship_list()}
    ship_controllers = [MinerShipController(ships["SHOCSOARES-1"], "X1-VD53-XD5D",
                                "X1-VD53-H45", ["COPPER_ORE", "ALUMINUM_ORE", "IRON_ORE"])]
    app = SpaceTraders(ships, ship_controllers)
    app.run()