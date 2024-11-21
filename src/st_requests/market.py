

from datetime import timedelta
from logging import getLogger
from typing import List, Optional

from crud.market import create_update_market, get_market_from_db, get_markets_exchanging_db, get_markets_exporting_db, get_markets_importing_db, get_markets_in_system_db
from schemas.market import Market, TradeSymbol
from st_requests.request import get_request
from st_requests.waypoint import get_waypoint
from utils.utils import system_symbol_from_wp_symbol, utcnow

SYSTEM_BASE_URL = 'https://api.spacetraders.io/v2/systems'

logger = getLogger(__name__)


def __get_market_from_server(symbol: str) -> Optional[Market]:
    '''gets market from the server\n
    updates database\n
    then returns it'''
    response = get_request(f'{SYSTEM_BASE_URL}/{system_symbol_from_wp_symbol(symbol)}' +
                           f'/waypoints/{symbol}/market')
    if not response.ok:
        logger.warning("Get Contract request failed")
        return None
    js = response.json()
    market = Market.model_validate(js['data'])
    get_waypoint(market.symbol)
    return create_update_market(market)


def get_market(symbol: str, force: bool = False) -> Optional[Market]:
    '''gets market, from cache if possible'''
    if market := get_market_from_db(symbol) and not force:
        if market.last_updated - utcnow() < timedelta(minutes=5):
            return market
    return __get_market_from_server(symbol)


def get_markets_exporting(symbol: TradeSymbol) -> List[Market]:
    '''gets markets exporting good from cache'''
    return get_markets_exporting_db(symbol)


def get_markets_importing(symbol: TradeSymbol) -> List[Market]:
    '''gets markets importing good from cache'''

    return get_markets_importing_db(symbol)


def get_markets_exchanging(symbol: TradeSymbol) -> List[Market]:
    '''gets markets exchanging good from cache'''

    return get_markets_exchanging_db(symbol)


def get_markets_in_system(symbol: str) -> List[Market]:
    '''gets markets in system from cache'''
    return get_markets_in_system_db(symbol)
