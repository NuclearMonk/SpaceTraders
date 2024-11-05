import logging
from schemas.market import TradeSymbol
from st_requests.agent import get_my_agent
from st_requests.contract import get_all_contracts_from_server
from st_requests.market import get_market, get_markets_exchanging
from st_requests.ship import get_ship, get_ships, ship_dock, ship_navigate, ship_orbit
from st_requests.waypoint import get_system

logger = logging.getLogger(__name__)

logging.basicConfig(filename='data/logs/main.log', level=logging.INFO)


# print(get_my_agent())
# print(get_all_contracts_from_server())
# print(get_ships())
ship = get_ship("SHOCSOARES-1")
ship.orbit()