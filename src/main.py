import asyncio
import logging
from management.fleet_manager import FleetManager
from ui.base import SpaceTraders

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    # SpaceTraders().run()
    asyncio.run(FleetManager().run())
    