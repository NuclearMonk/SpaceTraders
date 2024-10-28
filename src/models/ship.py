from typing import List, Optional
from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.market import TradeSymbolModel
from schemas.market import TradeSymbol
from schemas.ship import Rotation, ShipEngineSymbol, ShipFrameSymbol, ShipModuleSymbol, ShipMountSymbol, ShipNavFlightMode, ShipNavStatus, ShipReactorSymbol, ShipRole

from . import Base


class ShipFuelConsumptionEventModel(Base):
    __tablename__ = "fuel_consumptions"
    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    ship_symbol: Mapped[str] = Column(Text(20), ForeignKey("ships.symbol"))
    amount: Mapped[int] = mapped_column(Integer)
    timestamp: Mapped[DateTime] = mapped_column(DateTime)


class RequirementsModel(Base):
    __tablename__ = "requirements"
    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    power: Mapped[int] = mapped_column(Integer)
    crew: Mapped[int] = mapped_column(Integer)
    slots: Mapped[int] = mapped_column(Integer)


class ShipFrameTypeModel(Base):
    __tablename__ = "ship_frame_types"
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


class ShipReactorTypeModel(Base):
    __tablename__ = "ship_reactor_types"
    symbol: Mapped[ShipReactorSymbol] = mapped_column(
        Enum(ShipReactorSymbol), primary_key=True)
    name: Mapped[str] = mapped_column(Text(20))
    description: Mapped[str] = mapped_column(Text)
    power_output: Mapped[int] = mapped_column(Integer)
    requirements_id: Mapped[int] = Column(
        Integer, ForeignKey(RequirementsModel.id))
    requirements: Mapped[RequirementsModel] = relationship()


class ShipEngineTypeModel(Base):
    __tablename__ = "ship_engine_types"
    symbol: Mapped[ShipEngineSymbol] = mapped_column(
        Enum(ShipEngineSymbol), primary_key=True)
    name: Mapped[str] = mapped_column(Text(20))
    description: Mapped[str] = mapped_column(Text)
    speed: Mapped[int] = mapped_column(Integer)
    requirements_id: Mapped[int] = Column(
        Integer, ForeignKey(RequirementsModel.id))
    requirements: Mapped[RequirementsModel] = relationship()


class MountDepositModel(Base):
    __tablename__ = "mount_deposits"
    mount_symbol: Mapped[ShipMountSymbol] = mapped_column(
        Enum(ShipMountSymbol), ForeignKey("ship_mount_types.symbol"), primary_key=True)
    trade_symbol: Mapped[TradeSymbol] = mapped_column(
        Enum(TradeSymbol), ForeignKey(TradeSymbolModel.symbol), primary_key=True)


class ShipMountTypeModel(Base):
    __tablename__ = "ship_mount_types"
    symbol: Mapped[ShipMountSymbol] = mapped_column(
        Enum(ShipMountSymbol), primary_key=True)
    name: Mapped[str] = mapped_column(Text(20))
    description: Mapped[Optional[str]] = mapped_column(Text)
    strength: Mapped[Optional[int]] = mapped_column(Integer)
    deposits: Mapped[List[TradeSymbolModel]] = relationship(
        secondary="mount_deposits", uselist=True)
    requirements_id: Mapped[int] = Column(
        Integer, ForeignKey(RequirementsModel.id))
    requirements: Mapped[RequirementsModel] = relationship()


class ShipModuleTypeModel(Base):
    __tablename__ = "ship_module_types"
    symbol: Mapped[ShipModuleSymbol] = mapped_column(
        Enum(ShipModuleSymbol), primary_key=True)
    name: Mapped[str] = mapped_column(Text(20))
    description: Mapped[Optional[str]] = mapped_column(Text)
    requirements_id: Mapped[int] = Column(
        Integer, ForeignKey(RequirementsModel.id))
    requirements: Mapped[RequirementsModel] = relationship()
    capacity: Mapped[Optional[int]] = mapped_column(Integer)
    range: Mapped[Optional[int]] = mapped_column(Integer)


class ShipModel(Base):
    __tablename__ = "ships"
    symbol: Mapped[str] = mapped_column(Text(20), primary_key=True)
    reg_name: Mapped[str] = mapped_column(Text(20))
    reg_factionSymbol: Mapped[str] = mapped_column(Text(20))
    reg_role: Mapped[ShipRole] = mapped_column(Text(20))
    nav_systemSymbol: Mapped[str] = mapped_column(Text(20))
    nav_waypointSymbol: Mapped[str] = mapped_column(Text(20))
    nav_status: Mapped[ShipNavStatus] = mapped_column(Enum(ShipNavStatus))
    nav_flightMode: Mapped[ShipNavFlightMode] = mapped_column(
        Enum(ShipNavFlightMode))
    nav_route_destination_symbol: Mapped[str] = ForeignKey("waypoints.symbol")
    nav_route_origin_symbol: Mapped[str] = ForeignKey("waypoints.symbol")
    nav_route_departure_time: Mapped[DateTime] = Column(
        DateTime(timezone=False))
    nav_route_arrival: Mapped[DateTime] = Column(DateTime(timezone=False))
    fuel_current: Mapped[int] = mapped_column(Integer)
    fuel_capacity: Mapped[int] = mapped_column(Integer)
    cooldown_expiration: Mapped[DateTime] = mapped_column(DateTime)
    cargo_units: Mapped[int] = mapped_column(Integer)
    cargo_capacity: Mapped[int] = mapped_column(Integer)
    inventory: Mapped[List["ShipCargoItemModel"]] = relationship(
        uselist=True, cascade="save-update, merge, delete, delete-orphan")
    frame: Mapped["ShipFrameModel"] = relationship()
    reactor: Mapped["ShipReactorModel"] = relationship()
    engine: Mapped["ShipEngineModel"] = relationship()
    mounts: Mapped[List[ShipMountTypeModel]] = relationship(
        secondary="ship_mounts", uselist=True)
    modules: Mapped[List[ShipModuleTypeModel]] = relationship(
        secondary="ship_modules", uselist=True)
    crew : Mapped["ShipCrewModel"] = relationship()


class ShipCargoItemModel(Base):
    __tablename__ = "ship_cargo_items"
    ship_symbol = Column(Text(20), ForeignKey(
        ShipModel.symbol), primary_key=True)
    trade_symbol = Column(Enum(TradeSymbol), ForeignKey(
        "trade_goods.symbol"), primary_key=True)
    units: Mapped[int] = mapped_column(Integer)


class ShipFrameModel(Base):
    __tablename__ = "ship_frames"
    ship_symbol = Column(Text(20), ForeignKey(
        ShipModel.symbol), primary_key=True)
    frame_symbol = Column(Enum(ShipFrameSymbol), ForeignKey(
        ShipFrameTypeModel.symbol))
    frame_type: Mapped[ShipFrameTypeModel] = relationship()
    condition: Mapped[float] = mapped_column(Float)
    integrity: Mapped[float] = mapped_column(Float)


class ShipReactorModel(Base):
    __tablename__ = "ship_reactors"
    ship_symbol = Column(Text(20), ForeignKey(
        ShipModel.symbol), primary_key=True)
    reactor_symbol = Column(Enum(ShipReactorSymbol), ForeignKey(
        ShipReactorTypeModel.symbol))
    reactor_type: Mapped[ShipReactorTypeModel] = relationship()
    condition: Mapped[float] = mapped_column(Float)
    integrity: Mapped[float] = mapped_column(Float)


class ShipEngineModel(Base):
    __tablename__ = "ship_engines"
    ship_symbol = Column(Text(20), ForeignKey(
        ShipModel.symbol), primary_key=True)
    engine_symbol = Column(Enum(ShipEngineSymbol), ForeignKey(
        ShipEngineTypeModel.symbol))
    engine_type: Mapped[ShipEngineTypeModel] = relationship()
    condition: Mapped[float] = mapped_column(Float)
    integrity: Mapped[float] = mapped_column(Float)


class ShipMountModel(Base):
    __tablename__ = "ship_mounts"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ship_symbol: Mapped[str] = mapped_column(ForeignKey(ShipModel.symbol))
    mount_symbol: Mapped[ShipMountSymbol] = mapped_column(ForeignKey(
        ShipMountTypeModel.symbol), type_=Enum(ShipMountSymbol))


class ShipModuleModel(Base):
    __tablename__ = "ship_modules"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ship_symbol: Mapped[str] = mapped_column(
        ForeignKey(ShipModel.symbol))
    module_symbol: Mapped[ShipModuleSymbol] = mapped_column(ForeignKey(
        ShipModuleTypeModel.symbol),
        type_=Enum(ShipModuleSymbol))


class ShipCrewModel(Base):
    __tablename__ = "ship_crews"
    ship_symbol = Column(Text(20), ForeignKey(
        ShipModel.symbol), primary_key=True)
    current: Mapped[int] = mapped_column(Integer)
    required: Mapped[int] = mapped_column(Integer)
    capacity: Mapped[int] = mapped_column(Integer)
    rotation: Mapped[Rotation] = mapped_column(Enum(Rotation))
    morale: Mapped[int] = mapped_column(Integer)
    wages: Mapped[int] = mapped_column(Integer)
