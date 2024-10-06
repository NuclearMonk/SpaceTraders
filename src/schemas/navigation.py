from login import HEADERS, SYSTEM_BASE_URL, get
from pydantic import BaseModel, TypeAdapter, ValidationError
from typing import List, Optional, Self
import math
from datetime import datetime

from utils.utils import system_symbol_from_wp_symbol


class WaypointTrait(BaseModel):
    symbol: str
    name: str
    description: str


class WaypointModifier(BaseModel):
    symbol: str
    name: str
    description: str


class WaypointFaction(BaseModel):
    symbol: str


class WaypointChart(BaseModel):
    waypointSymbol: Optional[str] = None
    submittedBy: Optional[str] = None
    submittedOn: Optional[datetime] = None


class Waypoint(BaseModel):
    symbol: str
    type: Optional[str] = None
    x: Optional[int] = None
    y: Optional[int] = None
    faction: Optional[WaypointFaction] = None
    traits: Optional[List[WaypointTrait]] = None
    modifiers: Optional[List[WaypointModifier]] = None
    orbitals: Optional[List[Self]] = None
    orbits: Optional[str] = None
    chart: Optional[WaypointChart] = None
    isUnderConstruction: Optional[bool] = None

    @property
    def system_symbol(self) -> str:
        return system_symbol_from_wp_symbol(self.symbol)
    
    def has_trait(self, trait_symbol:str)-> bool:
        return trait_symbol in set(trait.symbol for trait in self.traits)

    def distance_to(self, other: Self)-> float:
        return math.sqrt((self.x-other.x)**2 + (self.y-other.y)**2)


class System(BaseModel):
    symbol: str
    sectorSymbol: str
    type: str
    x: int
    y: int
    waypoints: List[Waypoint]
    factions: List[WaypointFaction]

    def get_filtered_waypoints(self, query, limit=20) -> List[Waypoint]:
        wps: list[Waypoint] = []
        ta = TypeAdapter(List[Waypoint])
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


def get_system_with_symbol(symbol: str) -> Optional[System]:
    if is_system_symbol(symbol):
        system_symbol = symbol
    else:
        system_symbol = system_symbol_from_wp_symbol(symbol)
    response = get(f"{SYSTEM_BASE_URL}/{system_symbol}")
    if response.ok:
        js = response.json()
        try:
            return System.model_validate(js["data"])
        except ValidationError as e:
            print(e)
            return None
    print(response)
    return None