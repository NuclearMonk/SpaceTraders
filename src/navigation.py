from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ValidationError
from login import HEADERS
from requests import get

from utils import print_json

SYSTEM_BASE_URL = "https://api.spacetraders.io/v2/systems/"


class WaypointTrait(BaseModel):
    symbol: str
    name: str
    description: str


class WaypointModifier(BaseModel):
    symbol: str
    name: str
    description: str

class WaypointSymbol(BaseModel):
    symbol: str

class WaypointFaction(BaseModel):
    symbol: str


class WaypointChart(BaseModel):
    waypointSymbol: str
    submittedBy: str
    submittedOn: datetime


class BaseWaypoint(WaypointSymbol):
    type: str
    x: int
    y: int

class ShipNavRouteWaypoint(BaseWaypoint):
    systemSymbol: str




class SystemWaypoint(BaseWaypoint):
    orbitals: List[WaypointSymbol]
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
    response = get(f"{SYSTEM_BASE_URL}/{symbol}")
    if response.ok:
        js = response.json()
        print_json(js)
        try:
            return System.model_validate(js["data"])
        except ValidationError as e:
            print(e)
            return None
    return None

if __name__ == "__main__":
    print(get_system_with_symbol("X1-VD53"))