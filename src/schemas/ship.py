from datetime import UTC, datetime, timedelta
from enum import Enum
import json
import logging
from typing import Dict, List, Optional, Self, Tuple
from pydantic import BaseModel, TypeAdapter, ValidationError
from crud.agent import create_agent
from crud.contract import create_update_contract
from crud.survey import store_survey
from crud.tradegood import get_good
from crud.transaction import get_create_transaction
from schemas.agent import Agent
from schemas.contract import Contract
from schemas.extraction import Extraction
from schemas.faction import FactionSymbol
from schemas.market import TradeGood, MarketTransaction, TradeSymbol
from schemas.navigation import ScannedSystem, Waypoint
from st_requests.contract import CONTRACTS_BASE_URL
from st_requests.request import patch_request, post_request
from st_requests.waypoint import get_system, get_waypoint
from utils.observable import Observable
from schemas.survey import Survey
from utils.utils import error_wrap, format_time_ms, success_wrap, time_until, console
from custom_logging import create_ship_logger
SHIPS_BASE_URL = 'https://api.spacetraders.io/v2/my/ships'


class ShipRole(str, Enum):
    '''
    The registered role of the ship
    '''

    FABRICATOR = 'FABRICATOR'
    HARVESTER = 'HARVESTER'
    HAULER = 'HAULER'
    INTERCEPTOR = 'INTERCEPTOR'
    EXCAVATOR = 'EXCAVATOR'
    TRANSPORT = 'TRANSPORT'
    REPAIR = 'REPAIR'
    SURVEYOR = 'SURVEYOR'
    COMMAND = 'COMMAND'
    CARRIER = 'CARRIER'
    PATROL = 'PATROL'
    SATELLITE = 'SATELLITE'
    EXPLORER = 'EXPLORER'
    REFINERY = 'REFINERY'


class ShipRegistration(BaseModel):
    '''
    The public registration information of the ship
    '''
    name: str
    factionSymbol: FactionSymbol
    role: ShipRole


class ShipFuel(BaseModel):
    '''
    Details of the ship's fuel tanks including how much fuel was consumed during the last transit or action.
    '''
    class ShipFuelConsumptionEvent(BaseModel):
        '''
        An object that only shows up when an action has consumed fuel in the process. Shows the fuel consumption data.
        '''
        amount: int
        timestamp: datetime
    current: int
    capacity: int
    consumed: ShipFuelConsumptionEvent


class Cooldown(BaseModel):
    '''
    A cooldown is a period of time in which a ship cannot perform certain actions.
    '''
    shipSymbol: str
    totalSeconds: int
    remainingSeconds: timedelta
    expiration: Optional[datetime] = datetime.now(UTC)

    @property
    def time_remaining(self):
        return time_until(self.expiration)


class ShipNavRoute(BaseModel):
    '''
    The routing information for the ship's most recent transit or current location.
    '''
    destination: Waypoint
    origin: Waypoint
    departureTime: datetime
    arrival: datetime

    @property
    def time_remaining(self):
        return time_until(self.arrival)


class ShipNavStatus(str, Enum):
    '''
    The current status of the ship
    '''
    IN_TRANSIT = 'IN_TRANSIT'
    IN_ORBIT = 'IN_ORBIT'
    DOCKED = 'DOCKED'

    def __str__(self) -> str:
        return self.value.replace('_', ' ')


class ShipNavFlightMode(str, Enum):
    '''
    The ship's set speed when traveling between waypoints or systems.
    '''
    DRIFT = 'DRIFT'
    STEALTH = 'STEALTH'
    CRUISE = 'CRUISE'
    BURN = 'BURN'

    def __str__(self) -> str:
        return self.value


class ShipNav(BaseModel):
    '''
    The navigation information of the ship.
    '''
    systemSymbol: str
    waypointSymbol: str
    status: ShipNavStatus
    flightMode: ShipNavFlightMode
    route: ShipNavRoute

    @property
    def live_status(self):
        """This should be the one being checked to make sure the ship is not falsely marked in transit"""
        if self.status != ShipNavStatus.IN_TRANSIT:
            return self.status
        if self.route.time_remaining == timedelta(0):
            self.waypointSymbol = self.route.destination.symbol
            self.systemSymbol = self.route.destination.system_symbol
            self.status = ShipNavStatus.IN_ORBIT
        return ShipNavStatus.IN_TRANSIT


class ShipCargoItem(TradeGood):
    '''
    The type of cargo item and the number of units.
    '''
    units: int


class ShipCargo(BaseModel):
    '''
    Ship cargo details.
    '''
    capacity: int
    units: int
    inventory: List[ShipCargoItem]

    @property
    def capacity_remaining(self):
        return self.capacity - self.units

    def items(self) -> Dict[TradeSymbol, int]:
        return {entry.symbol: entry.units for entry in self.inventory}

    def get_item_count(self, symbol: TradeSymbol) -> int:
        for item in self.inventory:
            if item.symbol == symbol:
                return item.units
        return 0


class ShipRequirements(BaseModel):
    '''
    The requirements for installation on a ship
    '''
    power: Optional[int] = 0
    crew: Optional[int] = 0
    slots: Optional[int] = 0


class ShipMountSymbol(str, Enum):
    '''
    Symbol of this mount.
    '''

    MOUNT_GAS_SIPHON_I = 'MOUNT_GAS_SIPHON_I'
    MOUNT_GAS_SIPHON_II = 'MOUNT_GAS_SIPHON_II'
    MOUNT_GAS_SIPHON_III = 'MOUNT_GAS_SIPHON_III'
    MOUNT_SURVEYOR_I = 'MOUNT_SURVEYOR_I'
    MOUNT_SURVEYOR_II = 'MOUNT_SURVEYOR_II'
    MOUNT_SURVEYOR_III = 'MOUNT_SURVEYOR_III'
    MOUNT_SENSOR_ARRAY_I = 'MOUNT_SENSOR_ARRAY_I'
    MOUNT_SENSOR_ARRAY_II = 'MOUNT_SENSOR_ARRAY_II'
    MOUNT_SENSOR_ARRAY_III = 'MOUNT_SENSOR_ARRAY_III'
    MOUNT_MINING_LASER_I = 'MOUNT_MINING_LASER_I'
    MOUNT_MINING_LASER_II = 'MOUNT_MINING_LASER_II'
    MOUNT_MINING_LASER_III = 'MOUNT_MINING_LASER_III'
    MOUNT_LASER_CANNON_I = 'MOUNT_LASER_CANNON_I'
    MOUNT_MISSILE_LAUNCHER_I = 'MOUNT_MISSILE_LAUNCHER_I'
    MOUNT_TURRET_I = 'MOUNT_TURRET_I'


class ShipMount(BaseModel):
    '''
    A mount is installed on the exterier of a ship.
    '''
    symbol: ShipMountSymbol
    name: str
    description: Optional[str] = None
    strength: Optional[int] = None
    deposits: Optional[List[TradeSymbol]] = None
    requirements: ShipRequirements


class ShipFrameSymbol(str, Enum):
    '''
    Symbol of the frame.
    '''

    FRAME_PROBE = 'FRAME_PROBE'
    FRAME_DRONE = 'FRAME_DRONE'
    FRAME_INTERCEPTOR = 'FRAME_INTERCEPTOR'
    FRAME_RACER = 'FRAME_RACER'
    FRAME_FIGHTER = 'FRAME_FIGHTER'
    FRAME_FRIGATE = 'FRAME_FRIGATE'
    FRAME_SHUTTLE = 'FRAME_SHUTTLE'
    FRAME_EXPLORER = 'FRAME_EXPLORER'
    FRAME_MINER = 'FRAME_MINER'
    FRAME_LIGHT_FREIGHTER = 'FRAME_LIGHT_FREIGHTER'
    FRAME_HEAVY_FREIGHTER = 'FRAME_HEAVY_FREIGHTER'
    FRAME_TRANSPORT = 'FRAME_TRANSPORT'
    FRAME_DESTROYER = 'FRAME_DESTROYER'
    FRAME_CRUISER = 'FRAME_CRUISER'
    FRAME_CARRIER = 'FRAME_CARRIER'


class ShipFrame(BaseModel):
    '''
    The frame of the ship. The frame determines the number of modules and mounting points of the ship, as well as base fuel capacity. As the condition of the frame takes more wear, the ship will become more sluggish and less maneuverable.
    '''
    symbol: ShipFrameSymbol
    name: str
    description: str
    condition: float
    integrity: float
    requirements: ShipRequirements
    moduleSlots: int
    mountingPoints: int
    fuelCapacity: int


class ShipReactorSymbol(str, Enum):
    '''
    Symbol of the reactor.
    '''

    REACTOR_SOLAR_I = 'REACTOR_SOLAR_I'
    REACTOR_FUSION_I = 'REACTOR_FUSION_I'
    REACTOR_FISSION_I = 'REACTOR_FISSION_I'
    REACTOR_CHEMICAL_I = 'REACTOR_CHEMICAL_I'
    REACTOR_ANTIMATTER_I = 'REACTOR_ANTIMATTER_I'


class ShipReactor(BaseModel):
    '''
    The reactor of the ship. The reactor is responsible for powering the ship's systems and weapons.
    '''
    symbol: ShipReactorSymbol
    name: str
    description: str
    condition: float
    integrity: float
    requirements: ShipRequirements
    powerOutput: int


class ShipEngineSymbol(str, Enum):
    '''
    The symbol of the engine.
    '''

    ENGINE_IMPULSE_DRIVE_I = 'ENGINE_IMPULSE_DRIVE_I'
    ENGINE_ION_DRIVE_I = 'ENGINE_ION_DRIVE_I'
    ENGINE_ION_DRIVE_II = 'ENGINE_ION_DRIVE_II'
    ENGINE_HYPER_DRIVE_I = 'ENGINE_HYPER_DRIVE_I'


class ShipEngine(BaseModel):
    '''
    The engine determines how quickly a ship travels between waypoints.
    '''
    symbol: ShipEngineSymbol
    name: str
    description: str
    condition: float
    integrity: float
    requirements: ShipRequirements
    speed: int


class ShipModuleSymbol(str, Enum):
    '''
    The symbol of the module.
    '''

    MODULE_MINERAL_PROCESSOR_I = 'MODULE_MINERAL_PROCESSOR_I'
    MODULE_GAS_PROCESSOR_I = 'MODULE_GAS_PROCESSOR_I'
    MODULE_CARGO_HOLD_I = 'MODULE_CARGO_HOLD_I'
    MODULE_CARGO_HOLD_II = 'MODULE_CARGO_HOLD_II'
    MODULE_CARGO_HOLD_III = 'MODULE_CARGO_HOLD_III'
    MODULE_CREW_QUARTERS_I = 'MODULE_CREW_QUARTERS_I'
    MODULE_ENVOY_QUARTERS_I = 'MODULE_ENVOY_QUARTERS_I'
    MODULE_PASSENGER_CABIN_I = 'MODULE_PASSENGER_CABIN_I'
    MODULE_MICRO_REFINERY_I = 'MODULE_MICRO_REFINERY_I'
    MODULE_ORE_REFINERY_I = 'MODULE_ORE_REFINERY_I'
    MODULE_FUEL_REFINERY_I = 'MODULE_FUEL_REFINERY_I'
    MODULE_SCIENCE_LAB_I = 'MODULE_SCIENCE_LAB_I'
    MODULE_JUMP_DRIVE_I = 'MODULE_JUMP_DRIVE_I'
    MODULE_JUMP_DRIVE_II = 'MODULE_JUMP_DRIVE_II'
    MODULE_JUMP_DRIVE_III = 'MODULE_JUMP_DRIVE_III'
    MODULE_WARP_DRIVE_I = 'MODULE_WARP_DRIVE_I'
    MODULE_WARP_DRIVE_II = 'MODULE_WARP_DRIVE_II'
    MODULE_WARP_DRIVE_III = 'MODULE_WARP_DRIVE_III'
    MODULE_SHIELD_GENERATOR_I = 'MODULE_SHIELD_GENERATOR_I'
    MODULE_SHIELD_GENERATOR_II = 'MODULE_SHIELD_GENERATOR_II'


class ShipModule(BaseModel):
    '''
    A module can be installed in a ship and provides a set of capabilities such as storage space or quarters for crew. Module installations are permanent.
    '''

    symbol: ShipModuleSymbol
    name: str
    description: str
    requirements: ShipRequirements
    capacity: Optional[int] = None
    range: Optional[int] = None


class Rotation(str, Enum):
    '''
    The rotation of crew shifts. A stricter shift improves the ship's performance. A more relaxed shift improves the crew's morale.
    '''

    STRICT = 'STRICT'
    RELAXED = 'RELAXED'


class ShipCrew(BaseModel):
    '''
    The ship's crew service and maintain the ship's systems and equipment.
    '''

    current: int
    required: int
    capacity: int
    rotation: Rotation
    morale: int
    wages: int


class ScannedShip(BaseModel):
    symbol: str
    registration: ShipRegistration
    nav: ShipNav
    frame: ShipFrame
    reactor: ShipReactor
    engine: ShipEngine
    mounts: List[ShipMount]


class Ship(ScannedShip, Observable):
    '''
    Ship details.
    '''
    fuel: ShipFuel
    cooldown: Cooldown
    cargo: ShipCargo

    modules: List[ShipModule]
    crew: ShipCrew

    def __init__(self,  **kwargs):
        super().__init__(**kwargs)

    def model_post_init(self, __context) -> None:
        create_ship_logger(self.symbol)

    def log(self, log: str, success: bool = False, error: bool = False) -> None:
        logger = logging.getLogger(self.symbol)
        msg = f'[{
            self.symbol}@{format_time_ms(datetime.now(UTC))}]{self.nav.waypointSymbol}: {log}'
        if success:
            logger.info(msg)
            console.print(success_wrap(msg))
        elif error:
            logger.error(msg)
            logger.error(self.model_dump_json())
            console.print(error_wrap(msg))
        else:
            console.print(msg)
            logger.info(msg)

    def add_cargo(self, good: TradeGood, units: int):
        self.log(f"Adding {units} of {good.symbol} from inventory")
        self.cargo.units += units
        for item in self.cargo.inventory:
            if item.symbol == good.symbol:
                item.units += units
                return
        self.cargo.inventory.append(ShipCargoItem(symbol=good.symbol,
                                                  name=good.name,
                                                  description=good.description,
                                                  units=units))
        self.update()

    def has_mount(self, mount_symbol: ShipMountSymbol) -> bool:
        for mount in self.mounts:
            if mount.symbol == mount_symbol:
                return True
        return False

    def remove_cargo(self, good: TradeGood, units: int):
        self.log(f"Removing {units} of {good.symbol} from inventory")
        self.cargo.units -= units
        for item in self.cargo.inventory:
            if item.symbol == good.symbol:
                item.units -= units
                if item.units == 0:
                    break
                return
        self.cargo.inventory.remove(item)
        self.update()

    def orbit(self) -> bool:
        self.log(f'Orbit')
        if self.nav.live_status != ShipNavStatus.DOCKED:
            self.log(f'Not Docked', error=True)
            return False
        response = post_request(f'{SHIPS_BASE_URL}/{self.symbol}/orbit')
        if not response or not response.ok:
            self.log("Orbit Ship request failed", error=True)
            return False
        js = response.json()
        try:
            nav = ShipNav.model_validate(js['data']['nav'])
            nav.route.origin = get_waypoint(nav.route.origin.symbol)
            nav.route.destination = get_waypoint(
                nav.route.destination.symbol)
            self.nav = nav
            self.update()
            self.log(f'Orbit Success', success=True)

            return True
        except ValidationError as e:
            self.log("Validation Failed", error=True)
            return False

    def dock(self) -> bool:
        self.log(f'Dock')
        if self.nav.live_status != ShipNavStatus.IN_ORBIT:
            self.log(f'Not In Orbit', error=True)
            return False
        response = post_request(f'{SHIPS_BASE_URL}/{self.symbol}/dock')
        if not response.ok:
            self.log("Dock Ship request failed", error=True)
            return False
        js = response.json()
        try:
            nav = ShipNav.model_validate(js['data']['nav'])
            nav.route.origin = get_waypoint(nav.route.origin.symbol)
            nav.route.destination = get_waypoint(nav.route.destination.symbol)
            self.nav = nav
            self.update()
            self.log(f'Dock Success', success=True)

            return True
        except ValidationError as e:
            self.log("Validation Failed", error=True)
            return False

    def survey(self) -> Tuple[bool, List[Survey]]:
        self.log(f'Survey')
        if self.nav.live_status != ShipNavStatus.IN_ORBIT:
            self.log(f'Not In Orbit', error=True)
            return False, []
        if self.cooldown.time_remaining > 0:
            self.log(f'Cooldown Not Up', error=True)
            return False, []

        response = post_request(
            f'{SHIPS_BASE_URL}/{self.symbol}/survey')
        if not response.ok:
            self.log("Survey request failed", error=True)
            return False, []
        ta = TypeAdapter(List[Survey])
        js = response.json()
        try:
            surveys = ta.validate_python(js['data']['surveys'])
            for survey in surveys:
                store_survey(survey)
            self.cooldown = Cooldown.model_validate(js['data']['cooldown'])
            self.update()
            self.log(f'Survey Success', success=True)
            return True, surveys
        except ValidationError as e:
            self.log(f'Validation Failed', error=True)
            return False, []

    def extract(self) -> Tuple[bool, Optional[Extraction]]:
        self.log(f'Extract')
        if self.nav.live_status != ShipNavStatus.IN_ORBIT:
            self.log('Not In Orbit', error=True)
            return False, None
        if self.cooldown.time_remaining.total_seconds() > 0:
            self.log('Cooldown Not Up', error=True)
            return False, None
        response = post_request(f'{SHIPS_BASE_URL}/{self.symbol}/extract',)
        js = response.json()
        if not response.ok:
            self.log("Extract request failed", error=True)
            return False, None
        try:
            new_cooldown = Cooldown.model_validate(
                js['data']['cooldown'])
            extraction = Extraction.model_validate(
                js['data']['extraction'])
            new_cargo = ShipCargo.model_validate(js['data']['cargo'])
            self.cooldown = new_cooldown
            self.cargo = new_cargo
            self.update()
            for event in js['data']['events']:
                self.log(f"Event: {event}")
            self.log(f'Extract Success', success=True)
            return True, extraction
        except ValidationError as e:
            self.log("Validation Failed", error=True)
            return False, None

    def extract_with_survey(self, survey: Survey) -> Tuple[bool, Optional[Extraction]]:
        self.log(f'Extract With Survey ({survey.signature})')
        if self.nav.live_status != ShipNavStatus.IN_ORBIT:
            self.log('Not In Orbit', error=True)
            return False, None
        if self.cooldown.time_remaining.total_seconds() > 0:
            self.log('Cooldown Not Up', error=True)
            return False, None
        response = post_request(f'{SHIPS_BASE_URL}/{self.symbol}/extract/survey',
                                data=survey.model_dump())

        js = response.json()
        if not response.ok:
            self.log("Extract with survey request failed", error=True)
            return False, None
        try:
            new_cooldown = Cooldown.model_validate(
                js['data']['cooldown'])
            extraction = Extraction.model_validate(
                js['data']['extraction'])
            new_cargo = ShipCargo.model_validate(js['data']['cargo'])
            self.cooldown = new_cooldown
            self.cargo = new_cargo
            self.update()
            for event in js['data']['events']:
                self.log(f"Event: {event}")
            self.log(f'Extract with Survey Success', success=True)
            return True, extraction
        except ValidationError as e:
            self.log("Validation Failed", error=True)
            return False, None

    def sell(self, good: TradeGood, units: int) -> Tuple[bool, Optional[MarketTransaction], Optional[Agent]]:
        self.log(f'Sell {units} Units of {good.symbol}')

        if self.nav.status != ShipNavStatus.DOCKED:
            self.log('Not Docked', error=True)
            return False, None, None
        payload = {'symbol': good.symbol,
                   'units': units}
        response = post_request(
            f'{SHIPS_BASE_URL}/{self.symbol}/sell', data=payload)
        if not response.ok:
            self.log(f'Sell Request Failed', error=True)
            return False, None, None
        js = response.json()
        try:
            transaction = MarketTransaction.model_validate(
                js['data']['transaction'])
            agent = Agent.model_validate(js['data']['agent'])
            self.cargo = ShipCargo.model_validate(js['data']['cargo'])
            self.update()
            self.log("Sell Success", success=True)
            return True, get_create_transaction(transaction), create_agent(agent)
        except ValidationError as e:
            self.log(f"Validation Failed", error=True)
            return False, None

    def purchase(self, good: TradeGood, units: int) -> Tuple[bool, Optional[MarketTransaction], Optional[Agent]]:
        self.log(f'Purchase {units} Units of {good.symbol}')

        if self.nav.status != ShipNavStatus.DOCKED:
            self.log('Not Docked', error=True)
            return False, None, None
        payload = {'symbol': good.symbol,
                   'units': units}
        response = post_request(
            f'{SHIPS_BASE_URL}/{self.symbol}/purchase', data=payload)
        if not response.ok:
            self.log(f'Purchase Request Failed', error=True)
            return False, None, None
        js = response.json()
        try:
            new_cargo = ShipCargo.model_validate(js['data']['cargo'])
            transaction = MarketTransaction.model_validate(
                js['data']['transaction'])
            agent = Agent.model_validate(js['data']['agent'])
            self.cargo = ShipCargo.model_validate(js['data']['cargo'])
            self.update()
            self.log("Purchase Success", success=True)
            return True, get_create_transaction(transaction), create_agent(agent)
        except ValidationError as e:
            self.log(f"Validation Failed", error=True)
            return False, None, None

    def jettison(self, good: TradeGood, units: int) -> bool:
        self.log(f'Jettison {units} units of {good.symbol}')

        if self.nav.status != ShipNavStatus.IN_ORBIT:
            self.log('Not in Orbit', error=True)
            return False
        payload = {'symbol': good.symbol,
                   'units': units}
        response = post_request(f'{SHIPS_BASE_URL}/{self.symbol}/jettison',
                                data=payload)
        js = response.json()
        if not response.ok:
            self.log(f'Jettison Request Failed', error=True)
            return False
        try:
            self.cargo = ShipCargo.model_validate(js['data']['cargo'])
            self.log('Jettison Successful', success=True)
            self.update()
            return True
        except ValidationError as e:
            self.log(f"Validation Failed", error=True)
            return False

    def refuel(self, units: int = 0) -> Tuple[bool, Optional[MarketTransaction], Optional[Agent]]:
        data = {}
        if units:
            self.log(f'Refuel {units} units')
            data['units'] = units
        else:
            self.log(f'Refuel to full')
        if self.nav.status != ShipNavStatus.DOCKED:
            self.log('Not Docked', error=True)
            return False, None, None
        response = post_request(
            f'{SHIPS_BASE_URL}/{self.symbol}/refuel', data=data)
        if not response.ok:
            self.log(f'Refuel Request Failed', error=True)
            return False, None, None
        js = response.json()
        try:
            new_fuel = ShipFuel.model_validate(js['data']['fuel'])
            transaction = MarketTransaction.model_validate(
                js['data']['transaction'])
            agent = Agent.model_validate(js['data']['agent'])
            self.fuel = new_fuel
            self.log('Refuel Successful', success=True)
            self.log(transaction)
            self.update()
            return True, get_create_transaction(transaction), create_agent(agent)
        except ValidationError as e:
            self.log(f'Validation Failed', error=True)
            return False, None, None

    def refuel_from_cargo(self, units: int = 0) -> bool:
        data = {'fromCargo': True}
        if units:
            self.log(f'Refuel  From Cargo {units} units')
            data['units'] = units
        else:
            self.log(f'Refuel To Full From Cargo')
        start_fuel = self.fuel.current
        response = post_request(
            f'{SHIPS_BASE_URL}/{self.symbol}/refuel', data=data)
        if not response.ok:
            self.log("Refuel request failed", error=True)
            return False
        js = response.json()
        try:
            agent = Agent.model_validate(js['data']['agent'])
            trans = MarketTransaction.model_validate(js['data']['transaction'])
            self.fuel = ShipFuel.model_validate(js['data']['fuel'])
            current_fuel = self.fuel.current
            consumed_fuel = current_fuel-start_fuel
            consumed_cargo_fuel = consumed_fuel // 100
            self.remove_cargo(get_good(TradeSymbol.FUEL), consumed_cargo_fuel)
            self.update()
            return True
        except ValidationError as e:
            self.log(f'Validation Failed', error=True)
            return False

    def jump(self, destination: Waypoint) -> Tuple[bool, Optional[MarketTransaction], Optional[Agent]]:
        self.log(f"Jumping  from {self.nav.waypointSymbol} to {
                 destination.symbol}")
        data = {'waypointSymbol': destination.symbol}
        response = post_request(
            f'{SHIPS_BASE_URL}/{self.symbol}/jump', data=data)
        if not response.ok:
            self.log("Jump request failed", error=True)
            return False, None, None
        js = response.json()
        try:
            trans = MarketTransaction.model_validate(js['data']['transaction'])
            agent = Agent.model_validate(js['data']['agent'])
            self.cargo = ShipNav.model_validate(js['data']['nav'])
            self.cooldown = Cooldown.model_validate(js['data']['cooldown'])
            self.update()
            return True, get_create_transaction(trans), create_agent(agent)
        except ValidationError as e:
            self.log(f'Validation Failed', error=True)
            return False, None, None

    def change_flight_mode(self, flight_mode: ShipNavFlightMode) -> bool:
        self.log(f'Change Flight Mode to {flight_mode}')
        data = {'flightMode': flight_mode}
        response = patch_request(
            f'{SHIPS_BASE_URL}/{self.symbol}/nav', data=data)
        if not response.ok:
            self.log("Change Flight Mode request failed", error=True)
            return False
        js = response.json()
        try:
            self.nav = ShipNav.model_validate(js['data'])
            self.log('Flight Mode Change Successful', success=True)
            self.update()
            return True
        except ValidationError as e:
            self.log(f'Validation Failed', error=True)
            return False

    def navigate(self, destination: Waypoint) -> bool:
        self.log(f'Navigate To {destination.symbol}')
        if self.nav.status != ShipNavStatus.IN_ORBIT:
            self.log('Not In Orbit', error=True)
            return False
        data = {'waypointSymbol': destination.symbol}
        response = post_request(
            f'{SHIPS_BASE_URL}/{self.symbol}/navigate', data=data)
        js = response.json()
        if not response.ok:
            self.log("Navigate request failed", error=True)
            return False
        try:
            self.fuel = ShipFuel.model_validate(js['data']['fuel'])
            self.nav = ShipNav.model_validate(js['data']['nav'])
            self.log(f'Navigation Successful Arriving at {
                self.nav.route.arrival}', success=True)
            for event in js['data']['events']:
                self.log(f"Event: {event}")
            self.update()
            return True
        except ValidationError as e:
            self.log(f'Validation Failed', error=True)
            return False

    def ship_warp(self, destination: Waypoint) -> bool:
        self.log(f"Warping  to {destination.symbol}")
        data = {'waypointSymbol': destination.symbol}
        response = post_request(
            f'{SHIPS_BASE_URL}/{self.symbol}/warp', data=data)
        if not response.ok:
            self.log("Warp request failed", error=True)
            return False
        js = response.json()
        try:
            self.fuel = ShipFuel.model_validate(js['data']['fuel'])
            self.nav = ShipNav.model_validate(js['data']['nav'])
            self.update()
            return True
        except ValidationError as e:
            self.log(f'Validation Failed', error=True)
            return False

    def ship_scan_systems(self) -> Tuple[bool, List[ScannedSystem]]:
        self.log(f"Scanning For Systems")
        response = post_request(f'{SHIPS_BASE_URL}/{self.symbol}/scan/systems')
        if not response.ok:
            self.log("Scan System request failed")
            return False, []
        js = response.json()
        try:
            ta = TypeAdapter(List[ScannedSystem])
            self.cooldown = Cooldown.model_validate(js['data']['cooldown'])
            systems = ta.validate_python(js['data']['systems'])
            self.update()
            new_systems: List[ScannedSystem] = []
            for s in systems:
                ns = ScannedSystem.model_validate(get_system(s.symbol))
                ns.distance = s.distance
                new_systems.append(s)
            return True, new_systems
        except ValidationError as e:
            self.log(f'Validation Failed', error=True)
            return False, []

    def ship_scan_waypoints(self) -> Tuple[bool, List[Waypoint]]:
        self.log(f"{self.symbol} Scanning For Waypoints")
        response = post_request(
            f'{SHIPS_BASE_URL}/{self.symbol}/scan/waypoints')
        if not response or not response.ok:
            self.log("Scan Waypoints request failed", error=True)
            return False, []
        js = response.json()
        try:
            ta = TypeAdapter(List[Waypoint])
            self.cooldown = Cooldown.model_validate(js['data']['cooldown'])
            self.update()
            waypoints = ta.validate_python(js['data']['waypoints'])
            waypoints = [get_waypoint(wp.symbol) for wp in waypoints]
            return True, waypoints
        except ValidationError as e:
            self.log(f'Validation Failed', error=True)
            return False, []

    def ship_scan_ships(self) -> Tuple[bool, List[ScannedShip]]:
        self.log(f"Scanning For Ships")
        response = post_request(f'{SHIPS_BASE_URL}/{self.symbol}/scan/ships')
        if not response.ok:
            self.log("Scan Ships request failed", error=True)
            return False, []
        try:
            js = response.json()
            ta = TypeAdapter(List[ScannedShip])
            self.cooldown = Cooldown.model_validate(js['data']['cooldown'])
            ships = ta.validate_python(js['data']['ships'])
            self.update()
            return True, ships
        except ValidationError as e:
            self.log(f'Validation Failed', error=True)
            return False, []

    def transfer_cargo(self, target_ship: Self, good: TradeGood, units: int) -> bool:
        self.log(f"Transferring {units} units of {
                 good.symbol} to {target_ship.symbol}")
        if self.nav.live_status == ShipNavStatus.IN_TRANSIT:
            self.log("Ship is in Transit")
            return False
        if self.nav.live_status != target_ship.nav.live_status:
            self.log("Ships don't have the same ")
        data = {'tradeSymbol': good.symbol,
                'units': units,
                'shipSymbol': target_ship.symbol}
        response = post_request(
            f'{SHIPS_BASE_URL}/{self.symbol}/transfer', data=data)
        if not response.ok:
            self.log("Transfer Cargo request failed", error=True)
            return False
        js = response.json()
        try:
            self.cargo = ShipCargo.model_validate(js['data']['cargo'])
            target_ship.add_cargo(good, units)
            self.update()
            return True
        except ValidationError as e:
            self.log(f'Validation Failed', error=True)
            return False

    def negotiate_contract(self) -> Tuple[bool, Optional[Contract]]:
        self.log(f"Negotiating Contract")
        response = post_request(
            f'{SHIPS_BASE_URL}/{self.symbol}/negotiate/contract')
        if not response.ok:
            self.log("Negotiate Contract request failed", error=True)
            return False, None
        js = response.json()
        try:
            contract = Contract.model_validate_json(js['data']['contract'])
            contract.add_observer(create_update_contract)
            contract.update()
            return True, contract
        except ValidationError as e:
            self.log(f'Bad RESPONSE: {
                json.dumps(js, indent=1)}', error=True)
            self.log(e)
            return False, None

    def deliver_to_contract(self, contract: Contract, good: TradeGood, units: int) -> Tuple[bool, Contract]:
        self.log(f'Attempting To Deliver to  Contract ({contract.id})')
        if self.nav.status != ShipNavStatus.DOCKED:
            self.log('Is Nod Docked ', error=True)
            return False, None
        data = {
            'shipSymbol': self.symbol,
            'tradeSymbol': good.symbol,
            'units': units
        }
        response = post_request(
            f'{CONTRACTS_BASE_URL}/{contract.id}/deliver', data=data)
        js = response.json()
        if not response.ok:
            self.log("Deliver To Contract request failed", error=True)
            return False, contract
        try:
            self.cargo = ShipCargo.model_validate(js['data']['cargo'])
            self.update()
            new_contract = Contract.model_validate(js['data']['contract'])
            contract.terms = new_contract.terms
            contract.update()
            return True, contract
        except ValidationError as e:
            self.log(f'Validation Failed', error=True)
            return False, contract

    def refine(self, good: TradeGood) -> Tuple[bool, List[ShipCargoItem], List[ShipCargoItem]]:
        self.log(f"Refining {good.symbol}")
        data = {'produce': good.symbol}
        response = post_request(
            f'{SHIPS_BASE_URL}/{self.symbol}/refine', data=data)
        if not response.ok:
            self.log("Refine request failed", error=True)
            return False, [], []
        js = response.json()
        try:
            self.cargo = ShipCargo.model_validate(js['data']['cargo'])
            self.cooldown = Cooldown.model_validate(js['data']['cooldown'])
            consumed = []
            for item in js['data']['consumed']:
                good = get_good(item['tradeSymbol'])
                produced.append(ShipCargoItem(symbol=good.symbol,
                                              name=good.name,
                                              description=good.description,
                                              units=item['units']))
            produced = []
            for item in js['data']['produced']:
                good = get_good(item['tradeSymbol'])
                produced.append(ShipCargoItem(symbol=good.symbol,
                                              name=good.name,
                                              description=good.description,
                                              units=item['units']))
            return True, consumed, produced

        except ValidationError as e:
            self.log(f'Validation Failed', error=True)
            return False, [], []
