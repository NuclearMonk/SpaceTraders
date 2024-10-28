from asyncio import sleep
from datetime import UTC, datetime, timedelta
from enum import Enum
import json
import logging
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, TypeAdapter, ValidationError
from crud.contract import store_contract
from crud.survey import store_survey
from crud.transaction import store_transaction
from login import CONTRACTS_BASE_URL, HEADERS
from schemas.contract import Contract
from schemas.extraction import Extraction
from schemas.market import TradeGood, MarketTransaction, TradeSymbol
from schemas.navigation import Waypoint
from utils.observable import Observable
from schemas.survey import Survey
from utils.utils import error_wrap, format_time_ms, success_wrap, time_until, console
from requests import Response, get, post, patch
from pathfinding.pathfinding import calculate_route
from custom_logging import create_ship_logger
SHIPS_BASE_URL = 'https://api.spacetraders.io/v2/my/ships'



class ShipRole(str, Enum):
    """
    The registered role of the ship
    """

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
    """
    The public registration information of the ship
    """
    name: str
    factionSymbol: str
    role: ShipRole


class ShipFuel(BaseModel):
    """
    Details of the ship's fuel tanks including how much fuel was consumed during the last transit or action.
    """
    class ShipFuelConsumptionEvent(BaseModel):
        """
        An object that only shows up when an action has consumed fuel in the process. Shows the fuel consumption data.
        """
        amount: int
        timestamp: datetime
    current: int
    capacity: int
    consumed: ShipFuelConsumptionEvent


class Cooldown(BaseModel):
    """
    A cooldown is a period of time in which a ship cannot perform certain actions.
    """
    shipSymbol: str
    totalSeconds: timedelta
    remainingSeconds: timedelta
    expiration: Optional[datetime] = datetime.now(UTC)

    @property
    def time_remaining(self):
        return time_until(self.expiration)


class ShipNavRoute(BaseModel):
    """
    The routing information for the ship's most recent transit or current location.
    """
    destination: Waypoint
    origin: Waypoint
    departureTime: datetime
    arrival: datetime

    @property
    def time_remaining(self):
        return time_until(self.arrival)


class ShipNavStatus(str, Enum):
    """
    The current status of the ship
    """
    IN_TRANSIT = "IN_TRANSIT"
    IN_ORBIT = "IN_ORBIT"
    DOCKED = "DOCKED"

    def __str__(self) -> str:
        return self.value.replace("_", " ")


class ShipNavFlightMode(str, Enum):
    """
    The ship's set speed when traveling between waypoints or systems.
    """
    DRIFT = 'DRIFT'
    STEALTH = 'STEALTH'
    CRUISE = 'CRUISE'
    BURN = 'BURN'

    def __str__(self) -> str:
        return self.value


class ShipNav(BaseModel):
    """
    The navigation information of the ship.
    """
    systemSymbol: str
    waypointSymbol: str
    status: ShipNavStatus
    flightMode: ShipNavFlightMode
    route: ShipNavRoute


class ShipCargoItem(TradeGood):
    """
    The type of cargo item and the number of units.
    """
    units: int


class ShipCargo(BaseModel):
    """
    Ship cargo details.
    """
    capacity: int
    units: int
    inventory: List[ShipCargoItem]

    @property
    def capacity_remaining(self):
        return self.capacity - self.units

    def items(self) -> Dict[str, int]:
        return {entry.symbol: entry.units for entry in self.inventory}


class ShipRequirements(BaseModel):
    """
    The requirements for installation on a ship
    """
    power: Optional[int] = 0
    crew: Optional[int] = 0
    slots: Optional[int] = 0


class ShipMountSymbol(str, Enum):
    """
    Symbol of this mount.
    """

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
    """
    A mount is installed on the exterier of a ship.
    """
    symbol: ShipMountSymbol
    name: str
    description: Optional[str]= None
    strength: Optional[int]= None
    deposits: Optional[List[TradeSymbol]] = None
    requirements: ShipRequirements


class ShipFrameSymbol(str, Enum):
    """
    Symbol of the frame.
    """

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
    """
    The frame of the ship. The frame determines the number of modules and mounting points of the ship, as well as base fuel capacity. As the condition of the frame takes more wear, the ship will become more sluggish and less maneuverable.
    """
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
    """
    Symbol of the reactor.
    """

    REACTOR_SOLAR_I = 'REACTOR_SOLAR_I'
    REACTOR_FUSION_I = 'REACTOR_FUSION_I'
    REACTOR_FISSION_I = 'REACTOR_FISSION_I'
    REACTOR_CHEMICAL_I = 'REACTOR_CHEMICAL_I'
    REACTOR_ANTIMATTER_I = 'REACTOR_ANTIMATTER_I'


class ShipReactor(BaseModel):
    """
    The reactor of the ship. The reactor is responsible for powering the ship's systems and weapons.
    """
    symbol: ShipReactorSymbol
    name: str
    description: str
    condition: float
    integrity: float
    requirements: ShipRequirements
    powerOutput: int


class ShipEngineSymbol(str, Enum):
    """
    The symbol of the engine.
    """

    ENGINE_IMPULSE_DRIVE_I = 'ENGINE_IMPULSE_DRIVE_I'
    ENGINE_ION_DRIVE_I = 'ENGINE_ION_DRIVE_I'
    ENGINE_ION_DRIVE_II = 'ENGINE_ION_DRIVE_II'
    ENGINE_HYPER_DRIVE_I = 'ENGINE_HYPER_DRIVE_I'


class ShipEngine(BaseModel):
    """
    The engine determines how quickly a ship travels between waypoints.
    """
    symbol: ShipEngineSymbol
    name: str
    description: str
    condition: float
    integrity: float
    requirements: ShipRequirements
    speed: int


class ShipModuleSymbol(str, Enum):
    """
    The symbol of the module.
    """

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
    """
    A module can be installed in a ship and provides a set of capabilities such as storage space or quarters for crew. Module installations are permanent.
    """

    symbol: ShipModuleSymbol
    name: str
    description: str
    requirements: ShipRequirements
    capacity: Optional[int] = None
    range: Optional[int] = None


class Rotation(str, Enum):
    """
    The rotation of crew shifts. A stricter shift improves the ship's performance. A more relaxed shift improves the crew's morale.
    """

    STRICT = 'STRICT'
    RELAXED = 'RELAXED'


class ShipCrew(BaseModel):
    """
    The ship's crew service and maintain the ship's systems and equipment.
    """

    current: int
    required: int
    capacity: int
    rotation: Rotation
    morale: int
    wages: int


class Ship(BaseModel, Observable):
    """
    Ship details.
    """
    symbol: str
    registration: ShipRegistration
    nav: ShipNav
    fuel: ShipFuel
    cooldown: Cooldown
    cargo: ShipCargo
    frame: ShipFrame
    reactor: ShipReactor
    engine: ShipEngine
    mounts: List[ShipMount]
    modules: List[ShipModule]
    crew: ShipCrew

    def model_post_init(self, __context) -> None:
        create_ship_logger(self.symbol)

    def log(self, log: str, success: bool = False, error: bool = False) -> None:
        logger = logging.getLogger(self.symbol)
        msg = f"[{
            self.symbol}@{format_time_ms(datetime.now(UTC))}]{self.nav.waypointSymbol}: {log}"
        if success:
            logger.info(msg)
            console.print(success_wrap(msg))
        elif error:
            logger.error(msg)
            console.print(error_wrap(msg))
        else:
            console.print(msg)
            logger.info(msg)

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

    def survey(self) -> Optional[List[Survey]]:
        self.log(f"Attempting to Survey")
        if self.nav.status != ShipNavStatus.IN_ORBIT:
            self.log("Attempt Failed: Ship is NOT IN ORBIT", error=True)
            return None
        response = post(
            f"{SHIPS_BASE_URL}/{self.symbol}/survey", headers=HEADERS)
        if response.ok:
            ta = TypeAdapter(List[Survey])
            try:
                js = response.json()
                surveys = ta.validate_python(js["data"]["surveys"])
                for survey in surveys:
                    store_survey(survey)
                cooldown = Cooldown.model_validate(js["data"]["cooldown"])
                self.cooldown = cooldown
                self.update()
            except ValidationError as e:
                self.log(f"Bad RESPONSE: {json.dumps(
                    response.json(), indent=1)}", error=True)
            self.log("Survey Successful", success=True)
            self.log(surveys)
            return surveys
        else:
            self.log(f"Attempt Failed: \n{json.dumps(
                response.json(), indent=1)}", error=True)
            return None

    def extract(self, survey: Survey = None) -> Tuple[bool, Optional[Extraction]]:
        self.log(f"Attempting to Extract")
        if self.nav.status != ShipNavStatus.IN_ORBIT:
            self.log("Attempt Failed: Ship is NOT IN ORBIT", error=True)
            return False, None
        if self.cooldown.time_remaining.total_seconds() > 0:
            self.log("Attempt Failed: Ship is ON COOLDOWN", error=True)
            return False, None
        if survey:
            self.log(f"Using survey {survey.signature}")
            self.log(survey.deposits)
            response = post(f"{SHIPS_BASE_URL}/{self.symbol}/extract",
                            survey.model_dump_json(), headers=HEADERS)
        else:
            response = post(
                f"{SHIPS_BASE_URL}/{self.symbol}/extract", headers=HEADERS)

        js = response.json()
        if response.ok:
            try:
                new_cooldown = Cooldown.model_validate(
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

    def sell(self, good_symbol: str, units=-1) -> bool:
        if units == -1:
            units = self.cargo.items()[good_symbol]
        self.log(f"Attempting To Sell {units} Units of {good_symbol}")
        payload = {"symbol": good_symbol,
                   "units": units}
        if self.nav.status != ShipNavStatus.DOCKED:
            self.log("Attempt Failed: Ship is NOT DOCKED", error=True)
            return False
        units_left = units
        while units_left > 0:
            units_to_sell = units_left if units_left < 20 else 20
            units_left -= units_to_sell
            payload = {"symbol": good_symbol,
                       "units": units_to_sell}
            response = post(f"{SHIPS_BASE_URL}/{self.symbol}/sell",
                            json=payload, headers=HEADERS)
            js = response.json()
            if response.ok:
                try:
                    new_cargo = ShipCargo.model_validate(js["data"]["cargo"])
                    transaction = MarketTransaction.model_validate(
                        js["data"]["transaction"])
                    store_transaction(transaction)
                    self.cargo = new_cargo
                    self.log(transaction.model_dump_json(indent=2))
                    self.log("Sale Successful", success=True)
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
        return False

    def purchase(self, good_symbol: str, units=-1) -> bool:
        if units == -1:
            units = self.cargo.capacity_remaining
        self.log(f"Attempting To PURCHASE {units} Units of {good_symbol}")

        if self.nav.status != ShipNavStatus.DOCKED:
            self.log("Attempt Failed: Ship is NOT DOCKED", error=True)
            return False
        units_left = units
        while units_left > 0:
            units_to_purchase = units_left if units_left < 20 else 20
            units_left -= units_to_purchase
            payload = {"symbol": good_symbol,
                       "units": units_to_purchase}
            response = post(f"{SHIPS_BASE_URL}/{self.symbol}/purchase",
                            json=payload, headers=HEADERS)
            js = response.json()
            if response.ok:
                try:
                    new_cargo = ShipCargo.model_validate(js["data"]["cargo"])
                    transaction = MarketTransaction.model_validate(
                        js["data"]["transaction"])
                    store_transaction(transaction)
                    self.cargo = new_cargo
                    self.log(transaction.model_dump_json(indent=2))
                    self.log("Purchase Successful", success=True)
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
        return False

    def jettison(self, good_symbol, units=0) -> bool:
        if units == 0:
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
        self.log(json.dumps(js, indent=2))
        if response.ok:
            try:
                new_fuel = ShipFuel.model_validate(js["data"]["fuel"])
                transaction = MarketTransaction.model_validate(
                    js["data"]["transaction"])
                store_transaction(transaction)
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
        self.log(json.dumps(js, indent=2))
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

    async def navigate(self, destination: Waypoint) -> bool:
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

    def negotiate_contract(self) -> Optional[Contract]:
        response = post(
            f"{SHIPS_BASE_URL}/{self.symbol}/negotiate/contract", headers=HEADERS)
        if response.ok:
            js = response.json()
            try:
                contract = Contract.model_validate_json(js["data"]["contract"])
                store_contract(contract)
                return contract
            except ValidationError as e:
                self.log(f"Bad RESPONSE: {
                         json.dumps(js, indent=1)}", error=True)
                self.log(e)
                return None
        self.log(f"Attempt Failed:\n{json.dumps(
            js, indent=1)}", error=True)
        return None

    def deliver_to_contract(self, contract_id: str, trade_symbol: str, units: int) -> Optional[Contract]:
        self.log(f"Attempting To Deliver Contract {contract_id} Cargo")
        if self.nav.status != ShipNavStatus.DOCKED:
            self.log("Attempt Failed: Ship is NOT DOCKED", error=True)
            return None
        body = {
            "shipSymbol": self.symbol,
            "tradeSymbol": trade_symbol,
            "units": units
        }
        response = post(
            f"{CONTRACTS_BASE_URL}/{contract_id}/deliver", json=body, headers=HEADERS)
        js = response.json()
        if response.ok:
            try:
                new_cargo = ShipCargo.model_validate(js["data"]["cargo"])
                self.cargo = new_cargo
                contract = Contract.model_validate(js["data"]["contract"])
                store_contract(contract)
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

    async def route_navigate(self, destination: Waypoint, dock: bool = False) -> bool:
        if self.nav.status == ShipNavStatus.IN_TRANSIT:
            self.log("ERROR: Ship is in transit")
        route = calculate_route(
            self.nav.waypointSymbol, destination.symbol, self.fuel.capacity, self.fuel.current)
        if not route:
            return False
        self.log("Route Calculated\n" +
                 "\n".join(f"{wp.symbol} {refuel}" for wp, refuel in route))
        if len(route) > 1:
            wp, refuel = route[0]
            if refuel:
                if self.nav.status == ShipNavStatus.DOCKED:
                    self.refuel()
                    self.orbit()
                elif self.nav.status == ShipNavStatus.IN_ORBIT:
                    self.dock()
                    self.refuel()
                    self.orbit()
            for wp, refuel in route[1:-1]:
                await self.navigate(wp)
                if refuel:
                    self.dock()
                    self.refuel()
                    self.orbit()
            wp, refuel = route[-1]
            await self.navigate(wp)
            if dock:
                self.dock()
                if refuel:
                    self.refuel()
            elif refuel:
                self.dock()
                self.refuel()
                self.orbit()
        return True


def get_ship_list() -> List[Ship]:
    ta = TypeAdapter(List[Ship])
    ships = ta.validate_python(
        get(SHIPS_BASE_URL, headers=HEADERS).json()["data"])
    return ships
