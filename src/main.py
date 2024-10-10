import asyncio
import logging

from management.fleet_manager import FleetManager

logger = logging.getLogger(__name__)

ui = False
if __name__ == "__main__":
    logging.basicConfig(filename='data/logs/main.log', level=logging.INFO)
    manager = FleetManager()
    asyncio.run(manager.run())
