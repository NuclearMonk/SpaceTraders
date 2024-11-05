from datetime import datetime, timedelta
from typing import Any, List, Optional
from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.market import TradeGoodModel, TradeSymbolModel
from models.waypoint import WaypointModel
from schemas.faction import FactionSymbol
from schemas.market import TradeSymbol
from schemas.ship import Rotation, ShipEngineSymbol, ShipFrameSymbol, ShipModuleSymbol, ShipMountSymbol, ShipNavFlightMode, ShipNavStatus, ShipReactorSymbol, ShipRole

from . import Base


class RequirementsModel(Base):
    __tablename__ = 'requirements'
    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    power: Mapped[int] = mapped_column(Integer)
    crew: Mapped[int] = mapped_column(Integer)
    slots: Mapped[int] = mapped_column(Integer)

    def __init__(self, power, crew, slots, **kw: Any):
        super().__init__(**kw)
        self.power = power
        self.crew = crew
        self.slots = slots


class ShipFrameTypeModel(Base):
    __tablename__ = 'ship_frame_types'
    symbol: Mapped[ShipFrameSymbol] = mapped_column(
        Enum(ShipFrameSymbol), primary_key=True)
    name: Mapped[str] = mapped_column(Text(20))
    description: Mapped[str] = mapped_column(Text)
    module_slots: Mapped[int] = mapped_column(Integer)
    mounting_points: Mapped[int] = mapped_column(Integer)
    fuel_capacity: Mapped[int] = mapped_column(Integer)
    requirements_id: Mapped[int] = Column(
        Integer, ForeignKey(RequirementsModel.id))
    requirements: Mapped[RequirementsModel] = relationship()

    def __init__(self, symbol: ShipFrameSymbol, name: str,
                 description: str, module_slots: int, mounting_points: int,
                 fuel_capacity: int, requirements: RequirementsModel, **kw: Any):
        super().__init__(**kw)
        self.symbol = symbol
        self.name = name
        self.description = description
        self.module_slots = module_slots
        self.mounting_points = mounting_points
        self.fuel_capacity = fuel_capacity
        self.requirements = requirements


class ShipReactorTypeModel(Base):
    __tablename__ = 'ship_reactor_types'
    symbol: Mapped[ShipReactorSymbol] = mapped_column(
        Enum(ShipReactorSymbol), primary_key=True)
    name: Mapped[str] = mapped_column(Text(20))
    description: Mapped[str] = mapped_column(Text)
    power_output: Mapped[int] = mapped_column(Integer)
    requirements_id: Mapped[int] = Column(
        Integer, ForeignKey(RequirementsModel.id))
    requirements: Mapped[RequirementsModel] = relationship()

    def __init__(self, symbol: ShipReactorSymbol, name: str, description: str, powerOutput: int, requirements: RequirementsModel, **kw: Any):
        super().__init__(**kw)
        self.symbol = symbol
        self.name = name
        self.description = description
        self.power_output = powerOutput
        self.requirements = requirements


class ShipEngineTypeModel(Base):
    __tablename__ = 'ship_engine_types'
    symbol: Mapped[ShipEngineSymbol] = mapped_column(
        Enum(ShipEngineSymbol), primary_key=True)
    name: Mapped[str] = mapped_column(Text(20))
    description: Mapped[str] = mapped_column(Text)
    speed: Mapped[int] = mapped_column(Integer)
    requirements_id: Mapped[int] = Column(
        Integer, ForeignKey(RequirementsModel.id))
    requirements: Mapped[RequirementsModel] = relationship()

    def __init__(self, symbol: ShipEngineSymbol, name: str, description: str, speed: int, requirements: RequirementsModel, **kw: Any):
        super().__init__(**kw)
        self.symbol = symbol
        self.name = name
        self.description = description
        self.speed = speed
        self.requirements = requirements


class MountDepositModel(Base):
    __tablename__ = 'mount_deposits'
    mount_symbol: Mapped[ShipMountSymbol] = mapped_column(
        Enum(ShipMountSymbol), ForeignKey('ship_mount_types.symbol'), primary_key=True)
    trade_symbol: Mapped[TradeSymbol] = mapped_column(
        Enum(TradeSymbol), ForeignKey(TradeSymbolModel.symbol), primary_key=True)


class ShipMountTypeModel(Base):
    __tablename__ = 'ship_mount_types'
    symbol: Mapped[ShipMountSymbol] = mapped_column(
        Enum(ShipMountSymbol), primary_key=True)
    name: Mapped[str] = mapped_column(Text(20))
    description: Mapped[Optional[str]] = mapped_column(Text)
    strength: Mapped[Optional[int]] = mapped_column(Integer)
    deposits: Mapped[List[TradeSymbolModel]] = relationship(
        secondary='mount_deposits', uselist=True)
    requirements_id: Mapped[int] = Column(
        Integer, ForeignKey(RequirementsModel.id))
    requirements: Mapped[RequirementsModel] = relationship()

    def __init__(self, symbol: ShipMountSymbol, name: str, description: str,
                 strength: Optional[int], deposits: List[TradeSymbolModel],
                 requirements: RequirementsModel, **kw: Any):
        super().__init__(**kw)
        self.symbol = symbol
        self.name = name
        self.description = description
        self.strength = strength
        self.deposits = deposits
        self.requirements = requirements


class ShipModuleTypeModel(Base):
    __tablename__ = 'ship_module_types'
    symbol: Mapped[ShipModuleSymbol] = mapped_column(
        Enum(ShipModuleSymbol), primary_key=True)
    name: Mapped[str] = mapped_column(Text(20))
    description: Mapped[Optional[str]] = mapped_column(Text)
    capacity: Mapped[Optional[int]] = mapped_column(Integer)
    range: Mapped[Optional[int]] = mapped_column(Integer)
    requirements_id: Mapped[int] = Column(
        Integer, ForeignKey(RequirementsModel.id))
    requirements: Mapped[RequirementsModel] = relationship()

    def __init__(self, symbol: ShipMountSymbol, name: str, description: str,
                 capacity: Optional[int], range: Optional[int],
                 requirements: RequirementsModel, **kw: Any):
        super().__init__(**kw)
        self.symbol = symbol
        self.name = name
        self.description = description
        self.capacity = capacity
        self.range = range
        self.requirements = requirements


class ShipModel(Base):
    __tablename__ = 'ships'
    symbol: Mapped[str] = mapped_column(Text(20), primary_key=True)
    registration: Mapped['ShipRegistrationModel'] = relationship(
        back_populates='ship')
    nav: Mapped['ShipNavModel'] = relationship(back_populates='ship')
    fuel: Mapped['ShipFuelModel'] = relationship(back_populates='ship')
    cooldown: Mapped['CooldownModel'] = relationship(back_populates='ship')
    cargo: Mapped['ShipCargoModel'] = relationship(back_populates='ship')
    frame: Mapped['ShipFrameModel'] = relationship(back_populates='ship')
    reactor: Mapped['ShipReactorModel'] = relationship(back_populates='ship')
    engine: Mapped['ShipEngineModel'] = relationship(back_populates='ship')
    mounts: Mapped[List[ShipMountTypeModel]] = relationship(backref='ships',
                                                            secondary='ship_mounts', uselist=True)
    modules: Mapped[List[ShipModuleTypeModel]] = relationship(backref='ships',
                                                              secondary='ship_modules', uselist=True)
    crew: Mapped['ShipCrewModel'] = relationship(back_populates='ship')

    def __init__(self,
                 symbol: str,
                 registration: 'ShipRegistrationModel',
                 nav: 'ShipNavModel',
                 fuel: 'ShipFuelModel',
                 cooldown: 'CooldownModel',
                 cargo: 'ShipCargoModel',
                 frame: 'ShipFrameModel',
                 reactor: 'ShipReactorModel',
                 engine: 'ShipEngineModel',
                 mounts: 'ShipMountTypeModel',
                 modules: 'ShipModuleTypeModel',
                 crew: 'ShipCrewModel', ** kw: Any):
        super().__init__(**kw)
        self.symbol = symbol
        self.registration = registration
        self.nav = nav
        self.fuel = fuel
        self.cooldown = cooldown
        self.cargo = cargo
        self.frame = frame
        self.reactor = reactor
        self.engine = engine
        self.mounts = mounts
        self.modules = modules
        self.crew = crew


class ShipRegistrationModel(Base):
    __tablename__ = 'ship_registrations'
    ship_symbol = Column(Text(20), ForeignKey(
        ShipModel.symbol), primary_key=True)
    ship: Mapped[ShipModel] = relationship(back_populates='registration')
    name: Mapped[str] = mapped_column(Text(20))
    faction_symbol: Mapped[FactionSymbol] = mapped_column(Enum(FactionSymbol))
    role: Mapped[ShipRole] = mapped_column(Enum(ShipRole))

    def __init__(self,
                 name: str,
                 faction_symbol: FactionSymbol,
                 role: ShipRole, **kw: Any):
        super().__init__(**kw)
        self.name = name
        self.faction_symbol = faction_symbol
        self.role = role


class ShipNavRouteModel(Base):
    __tablename__ = 'ship_nav_routes'
    ship_symbol = Column(Text(20), ForeignKey(
        'ship_navs.ship_symbol'), primary_key=True)
    destination_symbol: Mapped[str] = Column(Text(20), ForeignKey(WaypointModel.symbol))
    destination: Mapped[WaypointModel] = relationship(foreign_keys='ShipNavRouteModel.destination_symbol')
    origin_symbol: Mapped[str] = Column(Text(20), ForeignKey(WaypointModel.symbol))
    origin: Mapped[WaypointModel] = relationship(foreign_keys='ShipNavRouteModel.origin_symbol')
    departure_time: Mapped[DateTime] = Column(DateTime(timezone=False))
    arrival: Mapped[DateTime] = Column(DateTime(timezone=False))

    def __init__(self,
                 destination: WaypointModel,
                 origin: WaypointModel,
                 departure_time: datetime,
                 arrival: datetime, **kw: Any):
        super().__init__(**kw)
        self.destination = destination
        self.origin = origin
        self.departure_time = departure_time
        self.arrival = arrival


class ShipNavModel(Base):
    __tablename__ = 'ship_navs'
    ship_symbol: Mapped[str] = Column(
        Text(20), ForeignKey(ShipModel.symbol), primary_key=True)
    ship: Mapped[ShipModel] = relationship(back_populates='nav')
    systemSymbol: Mapped[str] = mapped_column(Text(20))
    waypointSymbol: Mapped[str] = mapped_column(Text(20))
    status: Mapped[ShipNavStatus] = mapped_column(Enum(ShipNavStatus))
    flightMode: Mapped[ShipNavFlightMode] = mapped_column(
        Enum(ShipNavFlightMode))
    route: Mapped[ShipNavRouteModel] = relationship()

    def __init__(self,
                 systemSymbol: str,
                 waypointSymbol: str,
                 status: ShipNavStatus,
                 flightMode: ShipNavFlightMode,
                 route: ShipNavRouteModel, **kw: Any):
        super().__init__(**kw)
        self.systemSymbol = systemSymbol
        self.waypointSymbol = waypointSymbol
        self.status = status
        self.flightMode = flightMode
        self.route = route


class ShipFuelConsumptionEventModel(Base):
    __tablename__ = 'fuel_consumptions'
    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    ship_symbol: Mapped[str] = Column(
        Text(20), ForeignKey(ShipModel.symbol))
    amount: Mapped[int] = mapped_column(Integer)
    timestamp: Mapped[DateTime] = mapped_column(DateTime(timezone=False))

    def __init__(self, amount: int,
                 timestamp: datetime, **kw: Any):
        super().__init__(**kw)
        self.amount = amount
        self.timestamp = timestamp


class ShipFuelModel(Base):
    __tablename__ = 'ship_fuels'
    ship_symbol: Mapped[str] = Column(
        Text(20), ForeignKey(ShipModel.symbol), primary_key=True)
    ship: Mapped[ShipModel] = relationship(back_populates='fuel')
    current: Mapped[int] = mapped_column(Integer)
    capacity: Mapped[int] = mapped_column(Integer)
    last_consumed_id: Mapped[int] = Column(
        Text(20), ForeignKey(ShipFuelConsumptionEventModel.id))
    consumed: Mapped[ShipFuelConsumptionEventModel] = relationship()

    def __init__(self,
                 current: int,
                 capacity: int,
                 consumed: ShipFuelConsumptionEventModel, **kw: Any):
        super().__init__(**kw)
        self.current = current
        self.capacity = capacity
        self.consumed = consumed


class CooldownModel(Base):
    __tablename__ = 'ship_cooldowns'
    ship_symbol = Column(Text(20), ForeignKey(
        ShipModel.symbol), primary_key=True)
    ship: Mapped[ShipModel] = relationship(back_populates='cooldown')
    total_seconds: Mapped[int] = mapped_column(Integer)
    expiration: Mapped[DateTime] = mapped_column(DateTime(timezone=False))

    def __init__(self,
                 total_seconds: int,
                 expiration: datetime,
                 **kw: Any):
        super().__init__(**kw)
        self.total_seconds = total_seconds
        self.expiration = expiration


class ShipCargoModel(Base):
    __tablename__ = 'ship_cargos'
    ship_symbol = Column(Text(20), ForeignKey(
        ShipModel.symbol), primary_key=True)
    ship: Mapped[ShipModel] = relationship(back_populates='cargo')
    units: Mapped[int] = mapped_column(Integer)
    capacity: Mapped[int] = mapped_column(Integer)
    inventory: Mapped[List['ShipCargoItemModel']] = relationship(
        uselist=True, cascade='save-update, merge, delete, delete-orphan')

    def __init__(self,
                 units: int,
                 capacity: int,
                 inventory: List['ShipCargoItemModel'],
                 **kw: Any):
        super().__init__(**kw)
        self.units = units
        self.capacity = capacity
        self.inventory = inventory

class ShipCargoItemModel(Base):
    __tablename__ = 'ship_cargo_items'
    ship_symbol = Column(Text(20), ForeignKey(
        ShipCargoModel.ship_symbol), primary_key=True)
    trade_symbol = Column(Enum(TradeSymbol), ForeignKey(
        'trade_goods.symbol'), primary_key=True)
    good : Mapped[TradeGoodModel] = relationship()
    units: Mapped[int] = mapped_column(Integer)

    def __init__(self, good: TradeGoodModel, units: int, **kw: Any):
        super().__init__(**kw)
        self.good = good
        self.units = units


class ShipFrameModel(Base):
    __tablename__ = 'ship_frames'
    ship_symbol: Mapped[str] = Column(
        Text(20), ForeignKey(ShipModel.symbol), primary_key=True)
    ship: Mapped[ShipModel] = relationship(back_populates='frame')
    frame_symbol: Mapped[ShipFrameSymbol] = Column(
        Enum(ShipFrameSymbol), ForeignKey(ShipFrameTypeModel.symbol))
    frame_type: Mapped[ShipFrameTypeModel] = relationship()
    condition: Mapped[float] = mapped_column(Float)
    integrity: Mapped[float] = mapped_column(Float)

    def __init__(self, frame_type: ShipFrameTypeModel, condition: float, integrity: float, **kw: Any):
        super().__init__(**kw)
        self.frame_type = frame_type
        self.condition = condition
        self.integrity = integrity


class ShipReactorModel(Base):
    __tablename__ = 'ship_reactors'
    ship_symbol = Column(Text(20), ForeignKey(
        ShipModel.symbol), primary_key=True)
    ship: Mapped[ShipModel] = relationship(back_populates='reactor')
    reactor_symbol = Column(Enum(ShipReactorSymbol), ForeignKey(
        ShipReactorTypeModel.symbol))
    reactor_type: Mapped[ShipReactorTypeModel] = relationship()
    condition: Mapped[float] = mapped_column(Float)
    integrity: Mapped[float] = mapped_column(Float)

    def __init__(self, reactor_type: ShipReactorTypeModel, condition: float, integrity: float, **kw: Any):
        super().__init__(**kw)
        self.reactor_type = reactor_type
        self.condition = condition
        self.integrity = integrity


class ShipEngineModel(Base):
    __tablename__ = 'ship_engines'
    ship_symbol = Column(Text(20), ForeignKey(
        ShipModel.symbol), primary_key=True)
    ship: Mapped[ShipModel] = relationship(back_populates='engine')
    engine_symbol = Column(Enum(ShipEngineSymbol), ForeignKey(
        ShipEngineTypeModel.symbol))
    engine_type: Mapped[ShipEngineTypeModel] = relationship()
    condition: Mapped[float] = mapped_column(Float)
    integrity: Mapped[float] = mapped_column(Float)

    def __init__(self, engine_type: ShipEngineTypeModel, condition: float, integrity: float, **kw: Any):
        super().__init__(**kw)
        self.engine_type = engine_type
        self.condition = condition
        self.integrity = integrity


class ShipMountModel(Base):
    __tablename__ = 'ship_mounts'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ship_symbol: Mapped[str] = mapped_column(ForeignKey(ShipModel.symbol))
    mount_symbol: Mapped[ShipMountSymbol] = mapped_column(ForeignKey(
        ShipMountTypeModel.symbol), type_=Enum(ShipMountSymbol))


class ShipModuleModel(Base):
    __tablename__ = 'ship_modules'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ship_symbol: Mapped[str] = mapped_column(
        ForeignKey(ShipModel.symbol))
    module_symbol: Mapped[ShipModuleSymbol] = mapped_column(ForeignKey(
        ShipModuleTypeModel.symbol),
        type_=Enum(ShipModuleSymbol))


class ShipCrewModel(Base):
    __tablename__ = 'ship_crews'
    ship_symbol = Column(Text(20), ForeignKey(
        ShipModel.symbol), primary_key=True)
    ship: Mapped[ShipModel] = relationship(back_populates='crew')
    current: Mapped[int] = mapped_column(Integer)
    required: Mapped[int] = mapped_column(Integer)
    capacity: Mapped[int] = mapped_column(Integer)
    rotation: Mapped[Rotation] = mapped_column(Enum(Rotation))
    morale: Mapped[int] = mapped_column(Integer)
    wages: Mapped[int] = mapped_column(Integer)

    def __init__(self, current: int, required: int, capacity: int,
                 rotation: Rotation, morale: int, wages: int, **kw: Any):
        super().__init__(**kw)
        self.current = current
        self.required = required
        self.capacity = capacity
        self.rotation = rotation
        self.morale = morale
        self.wages = wages
