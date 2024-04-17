import asyncio
from typing import Dict
from ai.extract import extract_loop
from ship import Ship, get_ship_list
from ui import SpaceTraders

async def main():
    ships: Dict[str, Ship] = {ship.symbol: ship for ship in get_ship_list()}
    extract_task = asyncio.create_task(extract_loop(ships["SHOCSOARES-1"]))
    #app = SpaceTraders(ships)
    #await app.run()
    await extract_task

if __name__ == "__main__":
    asyncio.run(main())