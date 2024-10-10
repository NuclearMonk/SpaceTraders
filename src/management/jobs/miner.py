import asyncio
from typing import List, Optional
from job import Job
from schemas.navigation import Waypoint
from schemas.ship import Ship
from schemas.survey import Survey


class Mine(Job):

    def __init__(self, ship: Ship, look_for: List[str]) -> None:
        super().__init__(ship)
        self.look_for = frozenset(look_for)

    def start(self):
        self.ship.log("Mine Job Started")
        return True

    def end(self):
        self.ship.log("Miner Job Ended")
        return True

    def work(self):
        survey : Optional[Survey]= None
        while True:
            asyncio.sleep(0.2)
            match self.ship.cooldown.time_remaining, self.ship.cargo.capacity_remaining:
                case _, 0:  # no capacity remaining
                    if self.jettison_useless_cargo() == 0:
                        #cargo is full of useful stuff
                        # we are done
                        return True
                    else:
                        # we now have more space so, we keep going
                        continue
                case 0, _:
                    if survey and survey.is_valid:
                    
                    

    def jettison_useless_cargo(self) -> int:
        '''jettisons cargo not in loof_for, and returns the total amount of units dumped'''
        total: int = 0
        for symbol, units in self.ship.cargo.items():
            if symbol not in self.look_for:
                self.ship.jettison(symbol, units)
                total += units
        return total

    def get_surveys(self)-> Optional[Survey]:
        surveys = self.ship.survey()
        if surveys:
            sort_func = lambda x: x.rank_survey(self.look_for)
            surveys = list(filter(sort_func ,surveys))
            if surveys:
                surveys.sort(key = sort_func, reverse=True)
                return surveys[0]
        return None
        