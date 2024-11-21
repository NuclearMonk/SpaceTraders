

from logging import getLogger
from typing import Optional

from crud.system import create_update_system_db, get_system_db
from crud.waypoint import create_update_waypoint, get_waypoint_with_symbol
from schemas.navigation import System, Waypoint
from utils.utils import system_symbol_from_wp_symbol
from .request import get_request
SYSTEM_BASE_URL = 'https://api.spacetraders.io/v2/systems/'


logger = getLogger(__name__)


def __get_waypoint_from_server(symbol: str) -> Optional[Waypoint]:
    '''gets waypoint from server, updates cache'''
    logger.info(f'Getting waypoint with symbol {symbol} from server')
    split_symbol = symbol.split('-')
    system_symbol = f'{split_symbol[0]}-{split_symbol[1]}'
    response = get_request(
        f'{SYSTEM_BASE_URL}/{system_symbol}/waypoints/{symbol}')
    if not response or not response.ok:
        logger.warning("Get Waypoint request failed")
        return None
    js = response.json()
    waypoint = Waypoint.model_validate(js['data'])
    return create_update_waypoint(waypoint)


def get_waypoint(symbol: Optional[str]) -> Optional[Waypoint]:
    '''gets ship from the cache\n
    if not in cache then gets from server\n
    updates cache\n
    then returns them'''

    logger.info(f'Getting waypoint with symbol {symbol}')
    if symbol == None:
        return None
    if wp := get_waypoint_with_symbol(symbol):
        if wp.isUnderConstruction:
            logger.debug('Waypoint is under construction. Refreshing')
            return __get_waypoint_from_server(symbol)
            # modifiers can change so we check for those too
        if wp.modifiers:
            logger.info('Waypoint has MODIFIERS so refreshing')
            return __get_waypoint_from_server(symbol)
            # waypoints can become charted by other players
        if 'UNCHARTED' in {t.symbol for t in wp.traits}:
            logger.debug('Waypoint is UNCHARTED so refreshing')
            return __get_waypoint_from_server(symbol)
        return wp
    return __get_waypoint_from_server(symbol)


def get_system(system_symbol: str) -> Optional[System]:
    '''gets system from the database\n
    if not in database then gets from server\n
    updates database, and waypoints\n
    then returns it'''

    if system := get_system_db(system_symbol):
        system.waypoints = [get_waypoint(wp.symbol) for wp in system.waypoints]
        return system
    return __get_system_from_server(system_symbol)


def __get_system_from_server(symbol: str) -> Optional[Waypoint]:
    '''gets system from the server\n
    updates cache'''
    logger.info(f'Getting system with symbol {symbol} from server')
    response = get_request(f'{SYSTEM_BASE_URL}/{symbol}')

    if not response or not response.ok:
        logger.warning("Get System request failed")
        return None
    js = response.json()
    system = System.model_validate(js['data'])
    wps = [get_waypoint(wp.symbol) for wp in system.waypoints]
    system.waypoints = wps
    return create_update_system_db(system)


def __get_waypoint_from_server(symbol: str) -> Optional[Waypoint]:
    '''gets waypoint from the server\n
    updates cache'''
    logger.info(f'Getting waypoint with symbol {symbol} from server')
    system_symbol = system_symbol_from_wp_symbol(symbol)
    response = get_request(
        f'{SYSTEM_BASE_URL}/{system_symbol}/waypoints/{symbol}')
    if not response or not response.ok:
        logger.warning("Get Waypoint request failed")
        return None
    js = response.json()
    waypoint = Waypoint.model_validate(js['data'])
    return create_update_waypoint(waypoint)
