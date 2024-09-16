import asyncio
from management.fleet_manager import FleetManager
import logging

logger = logging.getLogger(__name__)

ui = False
if __name__ == "__main__":
    logging.basicConfig(filename='data/logs/main.log', level=logging.INFO)
    manager = FleetManager()
    if ui:
        #app = SpaceTraders(ships, ship_controllers)
        #app.run()
        pass
    else:
        asyncio.run(manager.run())
