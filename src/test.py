

from schemas.ship import get_ship_list
from crud.ship import store_ship_in_db

ships = get_ship_list()

for ship in ships:
    print(*ship.modules, sep="\n")
    store_ship_in_db(ship)
