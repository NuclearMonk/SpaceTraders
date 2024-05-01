from argparse import ArgumentParser, Namespace
from asyncio import sleep
from datetime import UTC, datetime, timedelta
from enum import Enum
import json
from typing import Callable, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field, TypeAdapter, ValidationError
from crud import get_waypoint_with_symbol, update_waypoint_cache
from login import CONTRACTS_BASE_URL, HEADERS
from schemas.contract import Contract
from schemas.market import Good, MarketTransaction
from schemas.navigation import Waypoint
from utils.observable import Observable
from schemas.survey import Survey
from utils.utils import error_wrap, format_time_ms, print_json, success_wrap, time_until, console
from requests import Response, get, post, patch


SHIPS_BASE_URL = 'https://api.spacetraders.io/v2/my/ships'


class ExtractionYield(BaseModel):
    symbol: str
    units: int


class Extraction(BaseModel):
    shipSymbol: str
    yield_field: ExtractionYield = Field(alias="yield")


class ShipRegistration(BaseModel):
    name: str
    factionSymbol: str
    role: str


class ShipFuel(BaseModel):
    class ShipFuelConsumptionEvent(BaseModel):
        amount: int
        timestamp: datetime
    current: int
    capacity: int
    consumed: ShipFuelConsumptionEvent


class ShipCooldown(BaseModel):
    shipSymbol: str
    totalSeconds: timedelta
    remainingSeconds: timedelta
    expiration: Optional[datetime] = datetime.now(UTC)

    @property
    def time_remaining(self):
        return time_until(self.expiration)


class ShipNavRoute(BaseModel):
    destination: Waypoint
    origin: Waypoint
    departureTime: datetime
    arrival: datetime

    @property
    def time_remaining(self):
        return time_until(self.arrival)


class ShipNavStatus(str, Enum):
    IN_TRANSIT = "IN_TRANSIT"
    IN_ORBIT = "IN_ORBIT"
    DOCKED = "DOCKED"

    def __str__(self) -> str:
        return self.value.replace("_", " ")


class ShipNavFlightMode(str, Enum):
    DRIFT = "DRIFT"
    STEALTH = "STEALTH"
    CRUISE = "CRUISE"
    BURN = "BURN"

    def __str__(self) -> str:
        return self.value


class ShipNav(BaseModel):
    systemSymbol: str
    waypointSymbol: str
    status: ShipNavStatus
    flightMode: ShipNavFlightMode
    route: ShipNavRoute


class ShipCargoItem(Good):
    units: int


class ShipCargo(BaseModel):
    capacity: int
    units: int
    inventory: List[ShipCargoItem]

    @property
    def capacity_remaining(self):
        return self.capacity - self.units

    def items(self) -> Dict[str, int]:
        return {entry.symbol: entry.units for entry in self.inventory}


class ShipRequirements(BaseModel):
    power: Optional[int] = 0
    crew: Optional[int] = 0
    slots: Optional[int] = 0


class ShipMount(BaseModel):
    symbol: str
    name: str
    description: Optional[str]
    strength: Optional[int]
    deposits: Optional[List[str]] = None
    requirements: ShipRequirements

class ShipComponent(BaseModel):
    symbol :str
    name :str 
    description: str
    condition : float
    integrity :float
    requirements : ShipRequirements

class ShipFrame(ShipComponent):
    moduleSlots : int
    mountingPoints : int
    fuelCapacity : int
class ShipReactor(ShipComponent):
    powerOutput: int

class ShipEngine(ShipComponent):
    speed: int


class Ship(BaseModel, Observable):
    symbol: str
    registration: ShipRegistration
    nav: ShipNav
    fuel: ShipFuel
    cooldown: ShipCooldown
    cargo: ShipCargo
    frame: ShipFrame
    reactor: ShipReactor
    engine: ShipEngine
    mounts: List[ShipMount]
    logger: Optional[Callable[[str], None]] = Field(print, exclude=True)

    def log(self, log: str, success: bool = False, error: bool = False) -> None:
        msg = f"[{self.nav.waypointSymbol}@{format_time_ms(datetime.now(UTC))}]{
            self.symbol}: {log}"
        if success:
            self.logger(success_wrap(msg))
        elif error:
            self.logger(error_wrap(msg))
        else:
            self.logger(msg)

    def orbit(self) -> bool:
        self.log(f"Attempting to Orbit")
        if self.nav.status != ShipNavStatus.DOCKED:
            self.log("Attempt Failed: Ship is NOT DOCKED", error=True)
            return False
        response: Response = post(
            f"{SHIPS_BASE_URL}/{self.symbol}/orbit", headers=HEADERS)
        if response.ok:
            try:
                new_nav = ShipNav.model_validate(
                    response.json()["data"]["nav"])
                self.nav = new_nav
                self.update()
            except ValidationError as e:
                self.log(f"Bad RESPONSE: {json.dumps(
                    response.json(), indent=1)}", error=True)
            self.log("Orbit Successful", success=True)
            return True
        else:
            self.log(f"Attempt Failed: \n{json.dumps(
                response.json(), indent=1)}", error=True)
            return False

    def dock(self) -> bool:
        self.log(f"Attempting to Dock")
        if self.nav.status != ShipNavStatus.IN_ORBIT:
            self.log("Attempt Failed: Ship is NOT IN ORBIT", error=True)
            return False
        response: Response = post(
            f"{SHIPS_BASE_URL}/{self.symbol}/dock", headers=HEADERS)
        if response.ok:
            try:
                new_nav = ShipNav.model_validate(
                    response.json()["data"]["nav"])
                self.nav = new_nav
                self.update()
            except ValidationError as e:
                self.log(f"Bad RESPONSE: {json.dumps(
                    response.json(), indent=1)}", error=True)

            self.log("Dock Successful", success=True)
            return True
        else:
            self.log(f"Attempt Failed: \n{json.dumps(
                response.json(), indent=1)}", error=True)
            return False

    def survey(self) -> Tuple[bool, Optional[List[Survey]]]:
        self.log(f"Attempting to Survey")
        if self.nav.status != ShipNavStatus.IN_ORBIT:
            self.log("Attempt Failed: Ship is NOT IN ORBIT", error=True)
            return False, None
        response = post(
            f"{SHIPS_BASE_URL}/{self.symbol}/survey", headers=HEADERS)
        if response.ok:
            ta = TypeAdapter(List[Survey])
            try:
                js = response.json()
                surveys = ta.validate_python(js["data"]["surveys"])
                cooldown = ShipCooldown.model_validate(js["data"]["cooldown"])
                self.cooldown = cooldown
                self.update()
            except ValidationError as e:
                self.log(f"Bad RESPONSE: {json.dumps(
                    response.json(), indent=1)}", error=True)
            self.log("Survey Successful", success=True)
            self.log(surveys)
            return True, surveys
        else:
            self.log(f"Attempt Failed: \n{json.dumps(
                response.json(), indent=1)}", error=True)
            return False, None

    def extract(self, survey: Survey=None) -> Tuple[bool, Optional[Extraction]]:
        self.log(f"Attempting to Extract")
        if self.nav.status != ShipNavStatus.IN_ORBIT:
            self.log("Attempt Failed: Ship is NOT IN ORBIT", error=True)
            return False, None
        if self.cooldown.time_remaining.total_seconds() > 0:
            self.log("Attempt Failed: Ship is ON COOLDOWN", error=True)
            return False, None
        if survey:
            self.log(f"Using survey {survey.signature}")
            self.log( survey.model_dump_json(indent=2))
            self.log(survey.deposits)
            response = post(f"{SHIPS_BASE_URL}/{self.symbol}/extract",
                            survey.model_dump_json(), headers=HEADERS)
        else:
            response = post(
                f"{SHIPS_BASE_URL}/{self.symbol}/extract", headers=HEADERS)

        js = response.json()
        if response.ok:
            try:
                new_cooldown = ShipCooldown.model_validate(
                    js["data"]["cooldown"])
                extraction = Extraction.model_validate(
                    js["data"]["extraction"])
                new_cargo = ShipCargo.model_validate(js["data"]["cargo"])
                self.cooldown = new_cooldown
                self.cargo = new_cargo
                self.log(str(extraction))
                self.log("Extract Successful", success=True)
                self.update()
                return True, extraction
            except ValidationError as e:
                self.log(f"Bad RESPONSE: {
                         json.dumps(js, indent=1)}", error=True)
                self.log(e)
                return False, None
        else:
            self.log(f"Attempt Failed: \n{json.dumps(
                js, indent=1)}", error=True)
            return False, None

    def sell(self, good_symbol: str, units = -1) -> bool:
        if units == -1:
            units = self.cargo.items()[good_symbol]
        self.log(f"Attempting To Sell {units} Units of {good_symbol}")
        payload = {"symbol": good_symbol,
                   "units": units}
        if self.nav.status != ShipNavStatus.DOCKED:
            self.log("Attempt Failed: Ship is NOT DOCKED", error=True)
            return False
        response = post(f"{SHIPS_BASE_URL}/{self.symbol}/sell",
                        json=payload, headers=HEADERS)
        js = response.json()
        if response.ok:
            try:
                new_cargo = ShipCargo.model_validate(js["data"]["cargo"])
                transaction = MarketTransaction.model_validate(
                    js["data"]["transaction"])
                self.cargo = new_cargo
                self.log(js["data"]["transaction"])
                self.log("Sell Successful", success=True)
                self.update()
                return True
            except ValidationError as e:
                self.log(f"Bad RESPONSE: {
                         json.dumps(js, indent=1)}", error=True)
                self.log(e)
                return False
        else:
            self.log(f"Attempt Failed: \n{json.dumps(
                js, indent=1)}", error=True)
            return False

    def purchase(self, good_symbol: str, units = -1) -> bool:
        if units == -1:
            units = self.cargo.capacity_remaining
        self.log(f"Attempting To PURCHASE {units} Units of {good_symbol}")
        payload = {"symbol": good_symbol,
                   "units": units}
        if self.nav.status != ShipNavStatus.DOCKED:
            self.log("Attempt Failed: Ship is NOT DOCKED", error=True)
            return False
        response = post(f"{SHIPS_BASE_URL}/{self.symbol}/purchase",
                        json=payload, headers=HEADERS)
        js = response.json()
        if response.ok:
            try:
                new_cargo = ShipCargo.model_validate(js["data"]["cargo"])
                transaction = MarketTransaction.model_validate(
                    js["data"]["transaction"])
                self.cargo = new_cargo
                self.log(js["data"]["transaction"])
                self.log("Sell Successful", success=True)
                self.update()
                return True
            except ValidationError as e:
                self.log(f"Bad RESPONSE: {
                         json.dumps(js, indent=1)}", error=True)
                self.log(e)
                return False
        else:
            self.log(f"Attempt Failed: \n{json.dumps(
                js, indent=1)}", error=True)
            return False

    def jettison(self, good_symbol, units =0) -> bool:
        if units==0:
            units = self.cargo.items()[good_symbol]
        self.log(f"Attempting To Jettison {units} Units of {good_symbol}")
        payload = {"symbol": good_symbol,
                   "units": units}
        if self.nav.status != ShipNavStatus.IN_ORBIT:
            self.log("Attempt Failed: Ship is NOT IN ORBIT", error=True)
            return False
        response = post(f"{SHIPS_BASE_URL}/{self.symbol}/jettison",
                        json=payload, headers=HEADERS)
        js = response.json()
        if response.ok:
            try:
                new_cargo = ShipCargo.model_validate(js["data"]["cargo"])
                self.cargo = new_cargo
                self.log("Jettison Successful", success=True)
                self.update()
                return True
            except ValidationError as e:
                self.log(f"Bad RESPONSE: {
                         json.dumps(js, indent=1)}", error=True)
                self.log(e)
                return False
        else:
            self.log(f"Attempt Failed: \n{json.dumps(
                js, indent=1)}", error=True)
            return False

    def refuel(self) -> bool:
        self.log(f"Attempting To Refuel")
        if self.nav.status != ShipNavStatus.DOCKED:
            self.log("Attempt Failed: Ship is NOT DOCKED", error=True)
            return False
        response = post(
            f"{SHIPS_BASE_URL}/{self.symbol}/refuel", headers=HEADERS)
        js = response.json()
        print_json(js)
        if response.ok:
            try:
                new_fuel = ShipFuel.model_validate(js["data"]["fuel"])
                transaction = MarketTransaction.model_validate(
                    js["data"]["transaction"])
                self.fuel = new_fuel
                self.log("Refuel Successful", success=True)
                self.log(transaction)
                self.update()
                return True
            except ValidationError as e:
                self.log(f"Bad RESPONSE: {
                         json.dumps(js, indent=1)}", error=True)
                self.log(e)
                return False
        else:
            self.log(f"Attempt Failed: \n{json.dumps(
                js, indent=1)}", error=True)
            return False

    def change_flight_mode(self, flight_mode: ShipNavFlightMode) -> bool:
        self.log(f"Attempting To Change Flight Mode to {flight_mode}")
        data = {"flightMode": flight_mode}

        response = patch(
            f"{SHIPS_BASE_URL}/{self.symbol}/nav", json=data, headers=HEADERS)
        js = response.json()
        print_json(js)
        if response.ok:
            try:
                nav = ShipNav.model_validate(js["data"])
                self.nav = nav
                self.log("Flight Mode Change Successful", success=True)
                self.update()
                return True
            except ValidationError as e:
                self.log(f"Bad RESPONSE: {
                         json.dumps(js, indent=1)}", error=True)
                self.log(e)
                return False
        else:
            self.log(f"Attempt Failed: \n{json.dumps(
                js, indent=1)}", error=True)
            return False

    async def navigate(self, destination:Waypoint) -> bool:
        self.log(f"Attempting to Navigate To {destination.symbol}")
        if self.nav.status != ShipNavStatus.IN_ORBIT:
            self.log("Attempt Failed: Ship is NOT IN ORBIT", error=True)
            return False
        data = {"waypointSymbol": destination.symbol}
        response = post(f"{SHIPS_BASE_URL}/{self.symbol}/navigate",
                        headers=HEADERS, json=data)
        js = response.json()
        if response.ok:
            try:
                new_fuel = ShipFuel.model_validate(js["data"]["fuel"])
                new_nav = ShipNav.model_validate(js["data"]["nav"])
                self.fuel = new_fuel
                self.nav = new_nav
                self.log(f"Navigation Successful Arriving at {
                         self.nav.route.arrival}", success=True)
                self.update()
                await sleep(self.nav.route.time_remaining.total_seconds())
                self.nav.status = ShipNavStatus.IN_ORBIT
                return True
            except ValidationError as e:
                self.log(f"Bad RESPONSE: {
                         json.dumps(js, indent=1)}", error=True)
                self.log(e)
                return False
        else:
            self.log(f"Attempt Failed:\n{json.dumps(
                js, indent=1)}", error=True)
            return False
        
    def negotiate_contract(self)->None:
        response = post(f"{SHIPS_BASE_URL}/{self.symbol}/negotiate/contract", headers=HEADERS)
        print(response.ok)
        print_json(response.json())
    
    def deliver_to_contract(self, contract_id : str, trade_symbol:str, units:int) -> Optional[Contract]:
        self.log(f"Attempting To Deliver Contract {contract_id} Cargo")
        if self.nav.status != ShipNavStatus.DOCKED:
            self.log("Attempt Failed: Ship is NOT DOCKED", error=True)
            return None
        body = {
            "shipSymbol": self.symbol,
            "tradeSymbol": trade_symbol,
            "units" : units
        }
        response = post(
            f"{CONTRACTS_BASE_URL}/{contract_id}/deliver",json = body, headers=HEADERS)
        js = response.json()
        if response.ok:
            try:
                new_cargo = ShipCargo.model_validate(js["data"]["cargo"])
                self.cargo = new_cargo
                contract = Contract.model_validate(js["data"]["contract"])
                return contract
            except ValidationError as e:
                self.log(f"Bad RESPONSE: {
                         json.dumps(js, indent=1)}", error=True)
                self.log(e)
                return None
        else:
            self.log(f"Attempt Failed:\n{json.dumps(
                js, indent=1)}", error=True)
            return None
            


def get_ship_list() -> List[Ship]:
    ta = TypeAdapter(List[Ship])
    ships = ta.validate_python(
        get(SHIPS_BASE_URL, headers=HEADERS).json()["data"])
    return ships


def get_ship_with_symbol(symbol: str) -> Optional[Ship]:
    response: Response = get(f"{SHIPS_BASE_URL}/{symbol}", headers=HEADERS)
    if not response.ok:
        print(response)
        return None
    return Ship.model_validate(response.json()["data"])


# if __name__ == "__main__":
#     parser = ArgumentParser()
#     subparsers = parser.add_subparsers(dest="command")
#     ship_parser = subparsers.add_parser("ship")
#     list_parser = subparsers.add_parser("list")
#     ship_parser.add_argument("id", type=str)
#     ship_options = ship_parser.add_mutually_exclusive_group()
#     ship_options.add_argument("--negotiate", action="store_true")
#     ship_options.add_argument("-o", "--orbit", action="store_true")
#     ship_options.add_argument("-d", "--dock", action="store_true")
#     ship_options.add_argument("-r", "--refuel", action="store_true")
#     ship_options.add_argument("-n", "--navigate", type=str)
#     ship_options.add_argument("-p", "--patch_navigation",
#                               type=str, choices=["DRIFT", "STEALTH", "CRUISE", "BURN"])
#     ship_options.add_argument("-j", "--jettison", type=str)
#     extract_options = ship_options.add_argument_group()
#     extract_options.add_argument("-s", "--survey", action="store_true")
#     extract_options.add_argument("-e", "--extract", action="store_true")
#     args: Namespace = parser.parse_args()
#     match args.command:
#         case "list":
#             print(*(ship.model_dump_json(indent=2)
#                   for ship in get_ship_list()))
#         case "ship":
#             if args.id:
#                 ship: Ship = get_ship_with_symbol(args.id)
#                 ship.logger = console.print
#                 if args.orbit:
#                     ship.orbit()
#                 elif args.dock:
#                     ship.dock()
#                 elif args.navigate:
#                     ship.navigate(get_waypoint_with_symbol(args.navigate))
#                 elif args.patch_navigation:
#                     ship.change_flight_mode(
#                         ShipNavFlightMode(args.patch_navigation))
#                 elif args.survey:
#                     ship.survey()
#                 elif args.extract:
#                     ship.extract()
#                 elif args.refuel:
#                     ship.refuel()
#                 elif args.jettison:
#                     ship.jettison(args.jettison)
#                 elif args.negotiate:
#                     ship.negotiate_contract()
#                 else:
#                     print(f"{args.id}: SHIP DATA")
#                     print(ship.model_dump_json(indent=2))
