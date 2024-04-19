import argparse
from asyncio import sleep
from datetime import datetime
import math
from typing import List, Optional
from pydantic import BaseModel, TypeAdapter, ValidationError
from login import HEADERS, SYSTEM_BASE_URL, get

from utils.utils import print_json


class WaypointTrait(BaseModel):
    symbol: str
    name: str
    description: str


class WaypointModifier(BaseModel):
    symbol: str
    name: str
    description: str


class BaseWaypoint(BaseModel):
    symbol: str


class WaypointFaction(BaseModel):
    symbol: str


class WaypointChart(BaseModel):
    waypointSymbol: Optional[str]
    submittedBy: Optional[str]
    submittedOn: Optional[datetime]


class BasicWaypoint(BaseWaypoint):
    type: str
    x: int
    y: int


class ShipNavRouteWaypoint(BasicWaypoint):
    systemSymbol: str


class SystemWaypoint(BasicWaypoint):
    orbitals: List[BaseWaypoint]
    orbits: Optional[str] = None


class Waypoint(SystemWaypoint):
    faction: Optional[WaypointFaction]
    traits: List[WaypointTrait]
    modifiers: Optional[List[WaypointModifier]]
    chart: Optional[WaypointChart]
    isUnderConstruction: bool


class System(BaseModel):
    symbol: str
    sectorSymbol: str
    type: str
    x: int
    y: int
    waypoints: List[SystemWaypoint]
    factions: List[WaypointFaction]

    def get_filtered_waypoints(self, query, limit=20) -> List[Waypoint]:
        wps: list[SystemWaypoint] = []
        ta = TypeAdapter(List[SystemWaypoint])
        current = 0
        m = float("inf")
        page = 1
        while current < m:
            response = get(SYSTEM_BASE_URL + self.symbol +
                           f"/waypoints?{query}&page={page}&limit={limit}", headers=HEADERS)
            if response.ok:
                js = response.json()
                m = js["meta"]["total"]
                current += len(js["data"])
                page += 1
                new_wps = ta.validate_python(js["data"])
                wps.extend(new_wps)
                print(f"{current} out of {m}")
        return wps


def is_system_symbol(symbol: str) -> bool:
    return symbol.count("-") == 1


def split_symbol(symbol: str):
    return symbol.split("-")


def system_symbol_from_wp_symbol(symbol: str):

    sector, system, wp = symbol.split("-")
    return f"{sector}-{system}"


def get_waypoint_with_symbol(symbol: str) -> Optional[SystemWaypoint]:
    split_symbol = symbol.split("-")
    system_symbol = f"{split_symbol[0]}-{split_symbol[1]}"
    response = get(f"{SYSTEM_BASE_URL}/{system_symbol}/waypoints/{symbol}")
    if response.ok:
        js = response.json()
        try:
            return SystemWaypoint.model_validate(js["data"])
        except ValidationError as e:
            print(e)
            return None


def get_system_with_symbol(symbol: str) -> Optional[System]:
    if is_system_symbol(symbol):
        system_symbol = symbol
    else:
        system_symbol = system_symbol_from_wp_symbol(symbol)
    response = get(f"{SYSTEM_BASE_URL}/{system_symbol}")
    if response.ok:
        js = response.json()
        print_json(js)
        try:
            return System.model_validate(js["data"])
        except ValidationError as e:
            print(e)
            return None
    return None


def distance_betweenWaypoints(A: BasicWaypoint, B: BasicWaypoint) -> float:
    return math.sqrt((A.x-B.x)**2 + (A.y-B.y)**2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("symbol")
    parser.add_argument("-s", "--search")
    args = parser.parse_args()
    if args.symbol:
        nav_point = get_waypoint_with_symbol(args.symbol)
        system = get_system_with_symbol(args.symbol)
    if args.search:
        if wps := system.get_filtered_waypoints(args.search):
            wps.sort(key=lambda x: distance_betweenWaypoints(nav_point, x))
            for d in wps:
                print(d.symbol, d.x, d.y, distance_betweenWaypoints(nav_point, d))
        else:
            "ERROR GETTING SYSTEM DATA"
    elif system:
        print(system.model_dump_json(indent=2))
    else:
        "ERROR GETTING SYSTEM DATA"
