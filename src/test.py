import logging
from sqlalchemy import select
from models.ship import ShipModel
from schemas.ship import get_ship_list
from crud.ship import create_or_update_ship, get_ship
from st_requests.agent import get_my_agent

ships = get_ship_list()
logger = logging.getLogger(__name__)

logging.basicConfig(filename='data/logs/main.log', level=logging.DEBUG)
# for ship in ships:
#     create_or_update_ship(ship)

print(get_my_agent())