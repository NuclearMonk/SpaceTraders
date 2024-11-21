from enum import Enum
from login import HEADERS, SYSTEM_BASE_URL, get
from pydantic import BaseModel, TypeAdapter, ValidationError
from typing import List, Optional, Self
import math
from datetime import datetime

from schemas.faction import FactionSymbol
from utils.utils import system_symbol_from_wp_symbol


class WaypointTraitSymbol(str, Enum):
    """
    The unique identifier of the trait.
    """

    UNCHARTED = 'UNCHARTED'
    UNDER_CONSTRUCTION = 'UNDER_CONSTRUCTION'
    MARKETPLACE = 'MARKETPLACE'
    SHIPYARD = 'SHIPYARD'
    OUTPOST = 'OUTPOST'
    SCATTERED_SETTLEMENTS = 'SCATTERED_SETTLEMENTS'
    SPRAWLING_CITIES = 'SPRAWLING_CITIES'
    MEGA_STRUCTURES = 'MEGA_STRUCTURES'
    PIRATE_BASE = 'PIRATE_BASE'
    OVERCROWDED = 'OVERCROWDED'
    HIGH_TECH = 'HIGH_TECH'
    CORRUPT = 'CORRUPT'
    BUREAUCRATIC = 'BUREAUCRATIC'
    TRADING_HUB = 'TRADING_HUB'
    INDUSTRIAL = 'INDUSTRIAL'
    BLACK_MARKET = 'BLACK_MARKET'
    RESEARCH_FACILITY = 'RESEARCH_FACILITY'
    MILITARY_BASE = 'MILITARY_BASE'
    SURVEILLANCE_OUTPOST = 'SURVEILLANCE_OUTPOST'
    EXPLORATION_OUTPOST = 'EXPLORATION_OUTPOST'
    MINERAL_DEPOSITS = 'MINERAL_DEPOSITS'
    COMMON_METAL_DEPOSITS = 'COMMON_METAL_DEPOSITS'
    PRECIOUS_METAL_DEPOSITS = 'PRECIOUS_METAL_DEPOSITS'
    RARE_METAL_DEPOSITS = 'RARE_METAL_DEPOSITS'
    METHANE_POOLS = 'METHANE_POOLS'
    ICE_CRYSTALS = 'ICE_CRYSTALS'
    EXPLOSIVE_GASES = 'EXPLOSIVE_GASES'
    STRONG_MAGNETOSPHERE = 'STRONG_MAGNETOSPHERE'
    VIBRANT_AURORAS = 'VIBRANT_AURORAS'
    SALT_FLATS = 'SALT_FLATS'
    CANYONS = 'CANYONS'
    PERPETUAL_DAYLIGHT = 'PERPETUAL_DAYLIGHT'
    PERPETUAL_OVERCAST = 'PERPETUAL_OVERCAST'
    DRY_SEABEDS = 'DRY_SEABEDS'
    MAGMA_SEAS = 'MAGMA_SEAS'
    SUPERVOLCANOES = 'SUPERVOLCANOES'
    ASH_CLOUDS = 'ASH_CLOUDS'
    VAST_RUINS = 'VAST_RUINS'
    MUTATED_FLORA = 'MUTATED_FLORA'
    TERRAFORMED = 'TERRAFORMED'
    EXTREME_TEMPERATURES = 'EXTREME_TEMPERATURES'
    EXTREME_PRESSURE = 'EXTREME_PRESSURE'
    DIVERSE_LIFE = 'DIVERSE_LIFE'
    SCARCE_LIFE = 'SCARCE_LIFE'
    FOSSILS = 'FOSSILS'
    WEAK_GRAVITY = 'WEAK_GRAVITY'
    STRONG_GRAVITY = 'STRONG_GRAVITY'
    CRUSHING_GRAVITY = 'CRUSHING_GRAVITY'
    TOXIC_ATMOSPHERE = 'TOXIC_ATMOSPHERE'
    CORROSIVE_ATMOSPHERE = 'CORROSIVE_ATMOSPHERE'
    BREATHABLE_ATMOSPHERE = 'BREATHABLE_ATMOSPHERE'
    THIN_ATMOSPHERE = 'THIN_ATMOSPHERE'
    JOVIAN = 'JOVIAN'
    ROCKY = 'ROCKY'
    VOLCANIC = 'VOLCANIC'
    FROZEN = 'FROZEN'
    SWAMP = 'SWAMP'
    BARREN = 'BARREN'
    TEMPERATE = 'TEMPERATE'
    JUNGLE = 'JUNGLE'
    OCEAN = 'OCEAN'
    RADIOACTIVE = 'RADIOACTIVE'
    MICRO_GRAVITY_ANOMALIES = 'MICRO_GRAVITY_ANOMALIES'
    DEBRIS_CLUSTER = 'DEBRIS_CLUSTER'
    DEEP_CRATERS = 'DEEP_CRATERS'
    SHALLOW_CRATERS = 'SHALLOW_CRATERS'
    UNSTABLE_COMPOSITION = 'UNSTABLE_COMPOSITION'
    HOLLOWED_INTERIOR = 'HOLLOWED_INTERIOR'
    STRIPPED = 'STRIPPED'


class WaypointTrait(BaseModel):
    symbol: WaypointTraitSymbol
    name: str
    description: str


class WaypointModifierSymbol(str, Enum):
    """
    The unique identifier of the modifier.
    """

    STRIPPED = 'STRIPPED'
    UNSTABLE = 'UNSTABLE'
    RADIATION_LEAK = 'RADIATION_LEAK'
    CRITICAL_LIMIT = 'CRITICAL_LIMIT'
    CIVIL_UNREST = 'CIVIL_UNREST'


class WaypointModifier(BaseModel):
    symbol: WaypointModifierSymbol
    name: str
    description: str


class WaypointFaction(BaseModel):
    symbol: FactionSymbol


class WaypointChart(BaseModel):
    waypointSymbol: Optional[str] = None
    submittedBy: Optional[str] = None
    submittedOn: Optional[datetime] = None


class WaypointType(str, Enum):
    '''
    The type of waypoint.
    '''
    PLANET = 'PLANET'
    GAS_GIANT = 'GAS_GIANT'
    MOON = 'MOON'
    ORBITAL_STATION = 'ORBITAL_STATION'
    JUMP_GATE = 'JUMP_GATE'
    ASTEROID_FIELD = 'ASTEROID_FIELD'
    ASTEROID = 'ASTEROID'
    ENGINEERED_ASTEROID = 'ENGINEERED_ASTEROID'
    ASTEROID_BASE = 'ASTEROID_BASE'
    NEBULA = 'NEBULA'
    DEBRIS_FIELD = 'DEBRIS_FIELD'
    GRAVITY_WELL = 'GRAVITY_WELL'
    ARTIFICIAL_GRAVITY_WELL = 'ARTIFICIAL_GRAVITY_WELL'
    FUEL_STATION = 'FUEL_STATION'


class Waypoint(BaseModel):
    symbol: str
    type: Optional[WaypointType] = None
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

    def has_trait(self, trait_symbol: WaypointTraitSymbol) -> bool:
        return trait_symbol in set(trait.symbol for trait in self.traits)

    def distance_to(self, other: Self) -> float:
        return math.sqrt((self.x-other.x)**2 + (self.y-other.y)**2)


class SystemType(str, Enum):
    """
    The type of system.
    """

    NEUTRON_STAR = 'NEUTRON_STAR'
    RED_STAR = 'RED_STAR'
    ORANGE_STAR = 'ORANGE_STAR'
    BLUE_STAR = 'BLUE_STAR'
    YOUNG_STAR = 'YOUNG_STAR'
    WHITE_DWARF = 'WHITE_DWARF'
    BLACK_HOLE = 'BLACK_HOLE'
    HYPERGIANT = 'HYPERGIANT'
    NEBULA = 'NEBULA'
    UNSTABLE = 'UNSTABLE'




class System(BaseModel):
    symbol: str
    sectorSymbol: str
    type: SystemType
    x: int
    y: int
    waypoints: Optional[List[Waypoint]] = None
    factions: Optional[List[WaypointFaction]] = None

    def get_filtered_waypoints(self, query, limit=20) -> List[Waypoint]:
        wps: list[Waypoint] = []
        ta = TypeAdapter(List[Waypoint])
        current = 0
        m = float('inf')
        page = 1
        while current < m:
            response = get(SYSTEM_BASE_URL + self.symbol +
                           f'/waypoints?{query}&page={page}&limit={limit}', headers=HEADERS)
            if response.ok:
                js = response.json()
                m = js['meta']['total']
                current += len(js['data'])
                page += 1
                new_wps = ta.validate_python(js['data'])
                wps.extend(new_wps)
                print(f'{current} out of {m}')
        return wps


class ScannedSystem(System):
    distance: Optional[int] = 0

def is_system_symbol(symbol: str) -> bool:
    return symbol.count('-') == 1


def split_symbol(symbol: str):
    return symbol.split('-')


def get_system_with_symbol(symbol: str) -> Optional[System]:
    if is_system_symbol(symbol):
        system_symbol = symbol
    else:
        system_symbol = system_symbol_from_wp_symbol(symbol)
    response = get(f'{SYSTEM_BASE_URL}/{system_symbol}')
    if response.ok:
        js = response.json()
        try:
            return System.model_validate(js['data'])
        except ValidationError as e:
            print(e)
            return None
    print(response)
    return None
