from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


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
    waypointSymbol: str
    submittedBy: str
    submittedOn: datetime


class NavigationWaypoint(BaseModel):
    symbol: str
    type: str
    systemSymbol: str
    x: int
    y: int


class Waypoint(NavigationWaypoint):
    orbitals: List[str]
    orbits: Optional[str]
    faction: WaypointFaction
    traits: List[WaypointTrait]
    modifiers: List[WaypointModifier]
    chart: WaypointChart
    isUnderConstruction: bool


class System(BaseModel):
    symbol: str
    sectorSymbol: str
    type: str
    x: int
    y: int
    waypoints: List[Waypoint]
    factions: List[WaypointFaction]
