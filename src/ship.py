from argparse import ArgumentParser, Namespace
from collections import deque
from datetime import UTC, datetime, timedelta
from enum import Enum
import json
from typing import Any, Deque, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, TypeAdapter, ValidationError
from login import HEADERS
from market import Good, MarketTransaction
from navigation import NavigationWaypoint
from observable import Observable
from survey import Survey
from utils import error_wrap, format_time_ms, print_json, success_wrap, time_until
from requests import Response, get, post, patch
from waypoint import WaypointSymbol


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
    destination: NavigationWaypoint
    origin: NavigationWaypoint
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


class Ship(BaseModel, Observable):
    symbol: str
    registration: ShipRegistration
    nav: ShipNav
    fuel: ShipFuel
    cooldown: ShipCooldown
    cargo: ShipCargo
    mounts: List[ShipMount]
    logs: Deque[str] = deque(maxlen=100)

    def log(self, log: str, success: bool = False, error: bool = False) -> None:
        msg = f"[{self.nav.waypointSymbol}@{format_time_ms(datetime.now(UTC))}]{
            self.symbol}: {log}"
        if success:
            self.logs.append(success_wrap(msg))
        elif error:
            self.logs.append(error_wrap(msg))
        else:
            self.logs.append(msg)
        self.update()

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
            self.log(f"Attempt Failed:\n{json.dumps(
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
            self.log(f"Attempt Failed:\n{json.dumps(
                response.json(), indent=1)}", error=True)
            return False, None

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
            self.log(f"Attempt Failed:\n{json.dumps(
                response.json(), indent=1)}", error=True)
            return False

    def sell(self, good_symbol) -> bool:
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
            self.log(f"Attempt Failed:\n{json.dumps(
                js, indent=1)}", error=True)
            return False

    def extract(self, survey=None) -> Tuple[bool, Optional[Extraction]]:
        self.log(f"Attempting to Extract")
        if self.nav.status != ShipNavStatus.IN_ORBIT:
            self.log("Attempt Failed: Ship is NOT IN ORBIT", error=True)
            return False, None
        if self.cooldown.time_remaining.total_seconds() > 0:
            self.log("Attempt Failed: Ship is ON COOLDOWN", error=True)
            return False, None
        if survey:
            response = post(f"{SHIPS_BASE_URL}/{self.symbol}/extract",
                            json=survey, headers=HEADERS)
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
            self.log(f"Attempt Failed:\n{json.dumps(
                js, indent=1)}", error=True)
            return False, None

    def jettison(self, good_symbol) -> bool:
        units = self.cargo.items()[good_symbol]
        self.log(f"Attempting To Jettison {units} Units of {good_symbol}")
        payload = {"symbol": good_symbol,
                   "units": units}
        if self.nav.status != ShipNavStatus.IN_ORBIT:
            self.log("Attempt Failed: Ship is NOT DOCKED", error=True)
            return False
        response = post(f"{SHIPS_BASE_URL}/{self.symbol}/jettison",
                        json=payload, headers=HEADERS)
        js = response.json()
        print_json(js)
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
            self.log(f"Attempt Failed:\n{json.dumps(
                js, indent=1)}", error=True)
            return False


def get_ship_list() -> List[Ship]:
    ta = TypeAdapter(List[Ship])
    ships = ta.validate_python(
        get(SHIPS_BASE_URL, headers=HEADERS).json()["data"])
    return ships


def get_ship_table() -> Dict[str, Ship]:
    return {ship.symbol: ship for ship in get_ship_list()}


def get_ship_info(id: str) -> Optional[Dict[str, Any]]:
    response: Response = get(f"{SHIPS_BASE_URL}/{id}", headers=HEADERS)
    return response.json()


def orbit_ship(id: str) -> Optional[Dict[str, Any]]:
    response = post(f"{SHIPS_BASE_URL}/{id}/orbit", headers=HEADERS)
    return response.json()


def dock_ship(id: str) -> Optional[Dict[str, Any]]:
    response = post(f"{SHIPS_BASE_URL}/{id}/dock", headers=HEADERS)
    return response.json()


def survey(id: str) -> Optional[Dict[str, Any]]:
    response = post(f"{SHIPS_BASE_URL}/{id}/survey", headers=HEADERS)
    return response.json()


def refuel(id: str) -> Optional[Dict[str, Any]]:
    response = post(f"{SHIPS_BASE_URL}/{id}/refuel", headers=HEADERS)
    return response.json()


def extract(id: str, survey=None) -> Optional[Dict[str, Any]]:
    if survey:
        response = post(f"{SHIPS_BASE_URL}/{id}/extract",
                        json=survey, headers=HEADERS)
    else:
        response = post(f"{SHIPS_BASE_URL}/{id}/extract", headers=HEADERS)
    return response.json()


def set_navigation_destination(id: str, destination: WaypointSymbol) -> Optional[Dict[str, Any]]:
    data = {"waypointSymbol": destination.waypoint_string}
    response = post(f"{SHIPS_BASE_URL}/{id}/navigate",
                    headers=HEADERS, json=data)
    return response.json()


def patch_navigation(id: str, speed: str) -> Optional[Dict[str, Any]]:
    data = {"flightMode": speed}
    response = patch(f"{SHIPS_BASE_URL}/{id}/nav",
                     headers=HEADERS, json=data)
    return response.json()


if __name__ == "__main__":
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    ship_parser = subparsers.add_parser("ship")
    list_parser = subparsers.add_parser("list")
    ship_parser.add_argument("id", type=str)
    ship_options = ship_parser.add_mutually_exclusive_group()
    ship_options.add_argument("-o", "--orbit", action="store_true")
    ship_options.add_argument("-d", "--dock", action="store_true")
    ship_options.add_argument("-r", "--refuel", action="store_true")
    ship_options.add_argument("-n", "--navigate", type=str)
    ship_options.add_argument("-p", "--patch_navigation",
                              type=str, choices=["DRIFT", "STEALTH", "CRUISE", "BURN"])
    ship_options.add_argument("-j", "--jettison", type=str)
    extract_options = ship_options.add_argument_group()
    extract_options.add_argument("-s", "--survey", action="store_true")
    extract_options.add_argument("-e", "--extract", action="store_true")
    args: Namespace = parser.parse_args()
    match args.command:
        case "list":
            print_json(get_ship_list())
        case "ship":
            if args.id:
                ship: Ship = Ship.model_validate(
                    get_ship_info(args.id)["data"])
                if args.orbit:
                    print(f"{args.id}: ATTEMPTING TO ORBIT")
                    print(ship.orbit())
                if args.dock:
                    print(f"{args.id}: ATTEMPTING TO DOCK")
                    print(ship.dock())
                elif args.navigate:
                    print(f"{args.id}:ATTEMPTING TO SET DESTINATION {
                          args.navigate}")
                    print_json(set_navigation_destination(args.id, WaypointSymbol(
                        *WaypointSymbol.split_symbol(args.navigate))))
                elif args.patch_navigation:
                    print(f"{args.id}:ATTEMPTING TO SET SPEED TO {
                          args.patch_navigation}")
                    print_json(patch_navigation(
                        args.id, args.patch_navigation))
                elif args.survey:
                    print(f"{args.id}:ATTEMPTING TO SURVEY")
                    print(ship.survey())
                elif args.extract:
                    print(f"{args.id}:ATTEMPTING TO EXTRACT")
                    print(ship.extract())
                elif args.refuel:
                    print(f"{args.id}:ATTEMPTING TO REFUEL")
                    print_json(refuel(args.id))
                elif args.jettison:
                    print(f"{args.id}:ATTEMPTING TO JETTISON")
                    print(ship.jettison(args.jettison))
                else:
                    print(f"{args.id}: SHIP DATA")
                    print_json(ship)
