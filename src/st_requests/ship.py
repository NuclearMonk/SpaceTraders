

from typing import Dict, List, Optional

from pydantic import TypeAdapter
from crud.ship import create_or_update_ship
from schemas.meta import Meta
from schemas.ship import Ship
from st_requests.request import get_request
from logging import getLogger

from st_requests.waypoint import get_waypoint
SHIPS_BASE_URL = 'https://api.spacetraders.io/v2/my/ships'

logger = getLogger(__name__)

__ships: Dict[str, Ship] = {}


def get_ships() -> List[Ship]:
    '''gets all the ships from the server then\nupdates them in the local database, then returns them'''
    logger.info("Getting all ships")
    ta = TypeAdapter(List[Ship])
    ships: list[Ship] = []
    current = 0
    total = float('inf')
    page = 1
    limit = 20
    while current < total:
        params = {'page': page, 'limit': limit}
        logger.info(f"Getting all ships({current} out of {total})")
        response = get_request(SHIPS_BASE_URL, params=params)
        if not response and not response.ok:
            logger.warning("List Ships request failed")
            break
        js = response.json()
        meta = Meta.model_validate(js['meta'])
        total = meta.total
        current += len(js['data'])
        page = meta.page+1
        new_ships = ta.validate_python(js['data'])
        ships.extend(new_ships)
    for ship in ships:
        __ships[ship.symbol] = ship
        ship.nav.route.origin = get_waypoint(ship.nav.route.origin.symbol)
        ship.nav.route.destination = get_waypoint(
            ship.nav.route.destination.symbol)
        ship.add_observer(create_or_update_ship)
        ship.update()
    return ships


def get_ship(symbol: str) -> Optional[Ship]:
    '''gets ship from the server\nr\n
    updates database\n
    then returns them'''
    if symbol in __ships:
        return __ships[symbol]

    logger.info("Getting ship {symbol}")
    response = get_request(f'{SHIPS_BASE_URL}/{symbol}')
    if not response.ok:
        logger.warning("Get Ship request failed")
        return None
    js = response.json()
    ship = Ship.model_validate(js['data'])
    ship.nav.route.origin = get_waypoint(ship.nav.route.origin.symbol)
    ship.nav.route.destination = get_waypoint(
        ship.nav.route.destination.symbol)
    ship.add_observer(create_or_update_ship)
    ship.update()
    __ships[symbol] = ship
    return ship
