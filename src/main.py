import logging
from management.fleet_manager import FleetManager


logger = logging.getLogger(__name__)

if __name__ == '__main__':
    FleetManager().run()