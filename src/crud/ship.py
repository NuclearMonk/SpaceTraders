from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from crud.tradegood import _get_trade_good, _get_trade_symbol_model
from models.ship import RequirementsModel, ShipCargoItemModel, ShipCrewModel, ShipEngineModel, ShipEngineTypeModel, ShipFrameModel, ShipFrameTypeModel, ShipModel, ShipModuleTypeModel, ShipMountTypeModel, ShipReactorModel, ShipReactorTypeModel
from schemas.ship import Ship, ShipCargoItem, ShipCrew, ShipEngine, ShipFrame, ShipModule, ShipMount, ShipReactor
from login import engine


def __cargo_model(ship_symbol: str, item: ShipCargoItem) -> ShipCargoItemModel:
    model = ShipCargoItemModel()
    model.ship_symbol = ship_symbol
    model.trade_symbol = item.symbol
    model.units = item.units
    return model


def __store_ship_in_db(ship: Ship, session: Session):
    model = ShipModel()
    model.symbol = ship.symbol
    model.reg_name = ship.registration.name
    model.reg_factionSymbol = ship.registration.factionSymbol
    model.reg_role = ship.registration.role
    model.nav_systemSymbol = ship.nav.systemSymbol
    model.nav_waypointSymbol = ship.nav.waypointSymbol
    model.nav_status = ship.nav.status
    model.nav_flightMode = ship.nav.flightMode
    model.nav_route_destination_symbol = ship.nav.route.destination
    model.nav_route_origin_symbol = ship.nav.route.origin
    model.nav_route_departure_time = ship.nav.route.departureTime
    model.nav_route_arrival = ship.nav.route.arrival
    model.fuel_capacity = ship.fuel.capacity
    model.fuel_current = ship.fuel.current
    model.cooldown_expiration = ship.cooldown.expiration
    model.cargo_units = ship.cargo.units
    model.cargo_capacity = ship.cargo.capacity
    model.inventory = [__cargo_model(ship.symbol, item)
                       for item in ship.cargo.inventory]
    model.frame = __create_frame(ship.frame, session)
    model.reactor = __create_reactor(ship.reactor, session)
    model.engine = __create_engine(ship.engine, session)
    model.mounts = [__get_mount_type(mount, session) for mount in ship.mounts]
    model.modules = [__get_module_type(module, session)
                     for module in ship.modules]
    model.crew= __create_crew(ship.crew, session)
    session.add(model)
    session.commit()


def __get_ship_from_db(ship_symbol: str, session: Session) -> Optional[ShipModel]:
    return session.scalar(select(ShipModel).where(ShipModel.symbol == ship_symbol))


def __update_ship(model: ShipModel, ship: Ship, session: Session):
    model.nav_systemSymbol = ship.nav.systemSymbol
    model.nav_waypointSymbol = ship.nav.waypointSymbol
    model.nav_status = ship.nav.status
    model.nav_flightMode = ship.nav.flightMode
    model.nav_route_destination_symbol = ship.nav.route.destination
    model.nav_route_origin_symbol = ship.nav.route.origin
    model.nav_route_departure_time = ship.nav.route.departureTime
    model.nav_route_arrival = ship.nav.route.arrival
    model.fuel_capacity = ship.fuel.capacity
    model.fuel_current = ship.fuel.current
    model.cooldown_expiration = ship.cooldown.expiration
    model.cargo_units = ship.cargo.units
    model.cargo_capacity = ship.cargo.capacity
    model.inventory = [__cargo_model(ship.symbol, item)
                       for item in ship.cargo.inventory]
    model.frame.condition = ship.frame.condition
    model.frame.integrity = ship.frame.integrity
    model.reactor.condition = ship.reactor.condition
    model.reactor.integrity = ship.reactor.integrity
    model.engine.condition = ship.engine.condition
    model.engine.integrity = ship.engine.integrity
    session.commit()


def __create_frame(frame: ShipFrame, session: Session) -> ShipFrameModel:
    """creates the ship frame association in the database"""
    frame_model = ShipFrameModel()
    frame_model.frame_type = __get_frame_type(frame, session)
    frame_model.condition = frame.condition
    frame_model.integrity = frame.integrity
    return frame_model


def __create_reactor(reactor: ShipReactor, session: Session) -> ShipFrameModel:
    """creates the ship reactor association in the database"""
    reactor_model = ShipReactorModel()
    reactor_model.reactor_type = __get_reactor_type(reactor, session)
    reactor_model.condition = reactor.condition
    reactor_model.integrity = reactor.integrity
    return reactor_model


def __create_engine(engine: ShipEngine, session: Session) -> ShipFrameModel:
    """creates the ship engine association in the database"""
    engine_model = ShipEngineModel()
    engine_model.engine_type = __get_engine_type(engine, session)
    engine_model.condition = engine.condition
    engine_model.integrity = engine.integrity
    return engine_model


def __create_crew(crew: ShipCrew, session: Session) -> ShipCrewModel:
    model = ShipCrewModel()
    model.current = crew.current
    model.required = crew.required
    model.capacity = crew.capacity
    model.rotation = crew.rotation
    model.morale = crew.morale
    model.wages = crew.wages
    return model


def __get_frame_type(frame: ShipFrame, session: Session) -> ShipFrameTypeModel:
    """gets the frame type from the database\ncreates one in the database if it doesn't exist already"""
    if frame_type_model := session.scalar(select(ShipFrameTypeModel).where(ShipFrameTypeModel.symbol == frame.symbol)):
        return frame_type_model
    frame_type_model = ShipFrameTypeModel()
    frame_type_model.symbol = frame.symbol
    frame_type_model.name = frame.name
    frame_type_model.description = frame.description
    frame_type_model.fuel_capacity = frame.fuelCapacity
    frame_type_model.module_slots = frame.moduleSlots
    frame_type_model.mounting_points = frame.mountingPoints
    requirements = RequirementsModel()
    requirements.crew = frame.requirements.crew
    requirements.power = frame.requirements.power
    requirements.slots = frame.requirements.slots
    frame_type_model.requirements = requirements
    session.add(frame_type_model)
    return frame_type_model


def __get_reactor_type(reactor: ShipReactor, session: Session) -> ShipReactorTypeModel:
    """gets the reactor type from the database\ncreates one in the database if it doesn't exist already"""
    if reactor_type_model := session.scalar(select(ShipReactorTypeModel).where(ShipReactorTypeModel.symbol == reactor.symbol)):
        return reactor_type_model
    reactor_type_model = ShipReactorTypeModel()
    reactor_type_model.symbol = reactor.symbol
    reactor_type_model.name = reactor.name
    reactor_type_model.description = reactor.description
    reactor_type_model.power_output = reactor.powerOutput
    requirements = RequirementsModel()
    requirements.crew = reactor.requirements.crew
    requirements.power = reactor.requirements.power
    requirements.slots = reactor.requirements.slots
    reactor_type_model.requirements = requirements
    session.add(reactor_type_model)
    return reactor_type_model


def __get_engine_type(engine: ShipEngine, session: Session) -> ShipEngineTypeModel:
    """gets the engine type from the database\ncreates one in the database if it doesn't exist already"""
    if engine_type_model := session.scalar(select(ShipEngineTypeModel).where(ShipEngineTypeModel.symbol == engine.symbol)):
        return engine_type_model
    engine_type_model = ShipEngineTypeModel()
    engine_type_model.symbol = engine.symbol
    engine_type_model.name = engine.name
    engine_type_model.description = engine.description
    engine_type_model.speed = engine.speed
    requirements = RequirementsModel()
    requirements.crew = engine.requirements.crew
    requirements.power = engine.requirements.power
    requirements.slots = engine.requirements.slots
    engine_type_model.requirements = requirements
    session.add(engine_type_model)
    return engine_type_model


def __get_mount_type(mount: ShipMount, session: Session) -> ShipMountTypeModel:
    """gets the mount type from the database\ncreates one in the database if it doesn't exist already"""
    if mount_type_model := session.scalar(select(ShipMountTypeModel).where(ShipMountTypeModel.symbol == mount.symbol)):
        return mount_type_model
    mount_type_model = ShipMountTypeModel()
    mount_type_model.symbol = mount.symbol
    mount_type_model.name = mount.name
    mount_type_model.description = mount.description
    mount_type_model.strength = mount.strength
    mount_type_model.deposits = [_get_trade_symbol_model(
        d, session) for d in mount.deposits] if mount.deposits else list()
    requirements = RequirementsModel()
    requirements.crew = mount.requirements.crew
    requirements.power = mount.requirements.power
    requirements.slots = mount.requirements.slots
    mount_type_model.requirements = requirements
    session.add(mount_type_model)

    return mount_type_model


def __get_module_type(module: ShipModule, session: Session) -> ShipModuleTypeModel:
    """gets the module type from the database\ncreates one in the database if it doesn't exist already"""
    if module_type_model := session.scalar(select(ShipModuleTypeModel).where(ShipModuleTypeModel.symbol == module.symbol)):
        return module_type_model
    module_type_model = ShipModuleTypeModel()
    module_type_model.symbol = module.symbol
    module_type_model.name = module.name
    module_type_model.description = module.description
    module_type_model.capacity = module.capacity
    module_type_model.range = module.range
    requirements = RequirementsModel()
    requirements.crew = module.requirements.crew
    requirements.power = module.requirements.power
    requirements.slots = module.requirements.slots
    module_type_model.requirements = requirements
    session.add(module_type_model)
    return module_type_model


def store_ship_in_db(ship: Ship):
    with Session(engine) as session:
        if model := __get_ship_from_db(ship.symbol, session):
            print("update")
            __update_ship(model, ship, session)
            return
        print("new")
        __store_ship_in_db(ship, session)
