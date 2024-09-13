import asyncio
from management.fleet_manager import FleetManager


ui = False
if __name__ == "__main__":
    manager = FleetManager()
    if ui:
        #app = SpaceTraders(ships, ship_controllers)
        #app.run()
        pass
    else:
        asyncio.run(manager.run())
