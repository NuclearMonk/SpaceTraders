import logging
from schemas.ship import get_ship_list

logger = logging.getLogger(__name__)



class FleetManager:
    def __init__(self) -> None:
        ships =  get_ship_list()
        print(ships)