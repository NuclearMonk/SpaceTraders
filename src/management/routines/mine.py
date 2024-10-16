import asyncio
from typing import List, Optional
from management.routines.routine import Routine
from schemas.navigation import Waypoint
from schemas.ship import Ship
from schemas.survey import Survey


class Mine(Routine):

    def __init__(self, look_for: List[str]) -> None:
        self.look_for = frozenset(look_for)

    def start(self, ship: Ship):
        ship.log("Mine: Job Started")
        return True

    def end(self, ship: Ship):
        ship.log("Mine: Job Ended")
        return True

    async def work(self, ship: Ship):
        survey: Optional[Survey] = None
        while True:
            await asyncio.sleep(0.2)
            print(ship.cooldown.time_remaining.total_seconds(), ship.cargo.capacity_remaining)

            match ship.cooldown.time_remaining.total_seconds(), ship.cargo.capacity_remaining:
                case _, 0:  # no capacity remaining
                    ship.log("Mine: Cargo Full")
                    if self.jettison_useless_cargo(ship) == 0:
                        # cargo is full of useful stuff
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
                        survey = self.get_survey(ship)
                        continue
                    elif survey and survey.is_valid:
                        ship.log("Mine: Try Extracting WITH Survey")
                        ship.extract(survey)
                        continue
                case t, _ if t > 0:
                    # Any cooldown means we need to just do nothing for the duration of the cooldown
                    ship.log(f"Mine: Waiting for Cooldown({t} seconds)")
                    await asyncio.sleep(t)
                    continue

    def jettison_useless_cargo(self, ship: Ship) -> int:
        '''jettisons cargo not in look_for, and returns the total amount of units dumped'''
        total: int = 0
        for symbol, units in ship.cargo.items().items():
            if symbol not in self.look_for:
                ship.jettison(symbol, units)
                total += units
        return total

    def get_survey(self, ship) -> Optional[Survey]:
        surveys = ship.survey()
        if surveys:
            def sort_func(x): return x.rank_survey(self.look_for)
            surveys = list(filter(sort_func, surveys))
            if surveys:
                surveys.sort(key=sort_func, reverse=True)
                return surveys[0]
        return None
