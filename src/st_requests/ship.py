

from typing import List, Optional, Tuple

from pydantic import TypeAdapter, ValidationError
from crud.agent import create_agent
from crud.ship import create_or_update_ship, update_ship
from crud.survey import store_survey
from crud.transaction import get_create_transaction
from schemas.agent import Agent
from schemas.extraction import Extraction
from schemas.market import MarketTransaction, TradeSymbol
from schemas.meta import Meta
from schemas.navigation import ScannedSystem, Waypoint
from schemas.ship import Cooldown, ScannedShip, Ship, ShipCargo, ShipFuel, ShipNav, ShipNavFlightMode
from schemas.survey import Survey
from st_requests.request import get_request, patch_request, post_request
from logging import getLogger

from st_requests.waypoint import get_system, get_waypoint
SHIPS_BASE_URL = 'https://api.spacetraders.io/v2/my/ships'

logger = getLogger(__name__)


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
        ship.nav.route.origin = get_waypoint(ship.nav.route.origin.symbol)
        ship.nav.route.destination = get_waypoint(
            ship.nav.route.destination.symbol)
        create_or_update_ship(ship)
    return ships


def get_ship(symbol: str) -> Optional[Ship]:
    '''gets ship from the server\nr\n
    updates database\n
    then returns them'''

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
    create_or_update_ship(ship)
    ship.add_observer(update_ship)
    return ship
