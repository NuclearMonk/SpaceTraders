import asyncio
from typing import List, Optional
from management.jobs.job import Job
from schemas.navigation import Waypoint
from schemas.ship import Ship
from schemas.survey import Survey


class Mine(Job):

    def __init__(self, look_for: List[str]) -> None:
        self.look_for = frozenset(look_for)

    def start(self, ship: Ship):
        ship.log("Mine: Job Started")
        return True

    def end(self, ship: Ship):
        ship.log("Mine: Job Ended")
        return True

    def work(self, ship: Ship):
        survey : Optional[Survey]= None
        while True:
            asyncio.sleep(0.2)
            match ship.cooldown.time_remaining, ship.cargo.capacity_remaining:
                case _, 0:  # no capacity remaining
                    ship.log("Mine: Cargo Full")
                    if self.jettison_useless_cargo(ship) == 0:
                        #cargo is full of useful stuff
                        # we are done
                        return True
                    else:
                        # we now have more space so, we keep going
                        ship.log("Mine: Jettisoned Cargo")
                        continue
                case 0, _:
                    # 0 cooldown means we need to mine
                    if survey and not survey.is_valid or not survey:
                        ship.log("Mine: Getting Fresh Survey")
                        survey = self.get_survey()
                    if survey and survey.is_valid:
                        ship.log("Mine: Try Extracting WITH Survey")
                        ship.extract(survey)
                case t,_:
                    # Any cooldown means we need to just do nothing for the duration of the cooldown
                    ship.log(f"Mine: Waiting for Cooldown({t} seconds)")
                    asyncio.sleep(t)

                    

    def jettison_useless_cargo(self, ship) -> int:
        '''jettisons cargo not in look_for, and returns the total amount of units dumped'''
        total: int = 0
        for symbol, units in ship.cargo.items():
            if symbol not in self.look_for:
                ship.jettison(symbol, units)
                total += units
        return total

    def get_survey(self, ship)-> Optional[Survey]:
        surveys = ship.survey()
        if surveys:
            sort_func = lambda x: x.rank_survey(self.look_for)
            surveys = list(filter(sort_func ,surveys))
            if surveys:
                surveys.sort(key = sort_func, reverse=True)
                return surveys[0]
        return None
        