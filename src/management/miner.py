

from datetime import timedelta
from schemas.navigation import Waypoint
from schemas.ship import Ship
from state_machine.state_machine import State, StateMachine
from state_machine.states.waiting import StateWaiting


class Miner:

    def __init__(self, ship: Ship, waypoint: Waypoint) -> None:
        self.ship = ship
        self.waypoint = waypoint
    
