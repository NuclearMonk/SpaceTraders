from datetime import UTC
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from crud.tradegood import _get_trade_symbol_model, _get_or_create_good
from crud.waypoint import _get_waypoint, _waypoint_to_schema
from models.ship import CooldownModel, RequirementsModel, ShipCargoItemModel, ShipCargoModel, ShipCrewModel, ShipEngineModel, ShipEngineTypeModel, ShipFrameModel, ShipFrameTypeModel, ShipFuelConsumptionEventModel, ShipFuelModel, ShipModel, ShipModuleTypeModel, ShipMountTypeModel, ShipNavModel, ShipNavRouteModel, ShipReactorModel, ShipReactorTypeModel, ShipRegistrationModel
from schemas.market import TradeSymbol
from schemas.ship import Cooldown, Rotation, Ship, ShipCargo, ShipCargoItem, ShipCrew, ShipEngine, ShipFrame, ShipFuel, ShipModule, ShipMount, ShipNav, ShipNavRoute, ShipReactor, ShipRegistration, ShipRequirements
from login import engine
from logging import getLogger

from utils.utils import time_until

logger = getLogger(__name__)


def __create_ship(ship: Ship, session: Session) -> ShipModel:
    '''creates a given ship the database if it doesn't exist already'''
    model = ShipModel(ship.symbol,
                      ShipRegistrationModel(
                          ship.registration.name,
                          ship.registration.factionSymbol,
                          ship.registration.role),
                      ShipNavModel(
                          ship.nav.systemSymbol,
                          ship.nav.waypointSymbol,
                          ship.nav.status,
                          ship.nav.flightMode,
                          ShipNavRouteModel(
                              _get_waypoint(
                                  ship.nav.route.destination.symbol, session),
                              _get_waypoint(
                                  ship.nav.route.origin.symbol, session),
                              ship.nav.route.departureTime,
                              ship.nav.route.arrival)),
                      ShipFuelModel(ship.fuel.current,
                                    ship.fuel.capacity,
                                    __get_fuel_consumption(ship.fuel.consumed,
                                                           session)),
                      CooldownModel(ship.cooldown.totalSeconds,
                                    ship.cooldown.expiration),
                      ShipCargoModel(
                          ship.cargo.units,
                          ship.cargo.capacity, []
                      ),
                      ShipFrameModel(
                          __get_frame_type(ship.frame, session),
                          ship.frame.condition,
                          ship.frame.integrity),
                      ShipReactorModel(
                          __get_reactor_type(ship.reactor, session),
                          ship.reactor.condition,
                          ship.reactor.integrity),
                      ShipEngineModel(
                          __get_engine_type(ship.engine, session),
                          ship.engine.condition,
                          ship.engine.integrity),
                      [],
                      [],
                      ShipCrewModel(
                          ship.crew.current,
                          ship.crew.required,
                          ship.crew.capacity,
                          ship.crew.rotation,
                          ship.crew.morale,
                          ship.crew.wages))
    session.add(model)
    ship.cargo.inventory = [__get_ship_cargo_item(item, session)
                            for item in ship.cargo.inventory]
    model.mounts = [__get_mount_type(mount, session) for mount in ship.mounts]
    model.modules = [__get_module_type(module, session)
                     for module in ship.modules]
    session.commit()
    return model


def __get_ship_from_db(ship_symbol: str, session: Session) -> Optional[ShipModel]:
    return session.scalar(select(ShipModel).where(ShipModel.symbol == ship_symbol))


def __update_ship(model: ShipModel, ship: Ship, session: Session) -> ShipModel:
    '''updates a given ship the database if it doesn't exist already'''
    model.nav.system_symbol = ship.nav.systemSymbol
    model.nav.waypoint_symbol = ship.nav.waypointSymbol
    model.nav.status = ship.nav.status
    model.nav.flight_mode = ship.nav.flightMode
    model.nav.route.destination = _get_waypoint(
        ship.nav.route.destination.symbol, session)
    model.nav.route.origin = _get_waypoint(
        ship.nav.route.origin.symbol, session)
    model.nav.route.departureTime = ship.nav.route.departureTime
    model.nav.route.arrival = ship.nav.route.arrival
    model.fuel.capacity = ship.fuel.capacity
    model.fuel.current = ship.fuel.current
    model.fuel.consumed = __get_fuel_consumption(ship.fuel.consumed, session)
    model.cooldown.expiration = ship.cooldown.expiration
    model.cargo.units = ship.cargo.units
    model.cargo.capacity = ship.cargo.capacity
    model.cargo.inventory = [__get_ship_cargo_item(item, session)
                             for item in ship.cargo.inventory]
    model.frame.condition = ship.frame.condition
    model.frame.integrity = ship.frame.integrity
    model.reactor.condition = ship.reactor.condition
    model.reactor.integrity = ship.reactor.integrity
    model.engine.condition = ship.engine.condition
    model.engine.integrity = ship.engine.integrity
    session.commit()
    return model


def __get_frame_type(frame: ShipFrame, session: Session) -> ShipFrameTypeModel:
    '''gets the frame type from the database\ncreates one in the database if it doesn't exist already'''
    if frame_type_model := session.scalar(select(ShipFrameTypeModel).where(ShipFrameTypeModel.symbol == frame.symbol)):
        return frame_type_model
    frame_type_model = ShipFrameTypeModel(
        frame.symbol,
        frame.name,
        frame.description,
        frame.fuelCapacity,
        frame.moduleSlots,
        frame.mountingPoints,
        RequirementsModel(frame.requirements.power,
                          frame.requirements.crew,
                          frame.requirements.slots))

    session.add(frame_type_model)
    return frame_type_model


def __get_reactor_type(reactor: ShipReactor, session: Session) -> ShipReactorTypeModel:
    '''gets the reactor type from the database\ncreates one in the database if it doesn't exist already'''
    if reactor_type_model := session.scalar(select(ShipReactorTypeModel).where(ShipReactorTypeModel.symbol == reactor.symbol)):
        return reactor_type_model
    reactor_type_model = ShipReactorTypeModel(
        reactor.symbol,
        reactor.name,
        reactor.description,
        reactor.powerOutput,
        RequirementsModel(
            reactor.requirements.power,
            reactor.requirements.crew,
            reactor.requirements.slots))
    session.add(reactor_type_model)
    return reactor_type_model


def __get_engine_type(engine: ShipEngine, session: Session) -> ShipEngineTypeModel:
    '''gets the engine type from the database\ncreates one in the database if it doesn't exist already'''
    if engine_type_model := session.scalar(select(ShipEngineTypeModel).where(ShipEngineTypeModel.symbol == engine.symbol)):
        return engine_type_model
    engine_type_model = ShipEngineTypeModel(
        engine.symbol,
        engine.name,
        engine.description,
        engine.speed,
        RequirementsModel(
            engine.requirements.power,
            engine.requirements.crew,
            engine.requirements.slots))
    session.add(engine_type_model)
    return engine_type_model


def __get_mount_type(mount: ShipMount, session: Session) -> ShipMountTypeModel:
    '''gets the mount type from the database\ncreates one in the database if it doesn't exist already'''
    if mount_type_model := session.scalar(select(ShipMountTypeModel).where(ShipMountTypeModel.symbol == mount.symbol)):
        return mount_type_model
    if mount.deposits:
        dep = [_get_trade_symbol_model(s, session)for s in mount.deposits]
    else:
        dep = list()
    mount_type_model = ShipMountTypeModel(
        mount.symbol,
        mount.name,
        mount.description,
        mount.strength,
        dep,
        RequirementsModel(
            mount.requirements.power,
            mount.requirements.crew,
            mount.requirements.slots)
    )
    session.add(mount_type_model)
    return mount_type_model


def __get_module_type(module: ShipModule, session: Session) -> ShipModuleTypeModel:
    '''gets the module type from the database\ncreates one in the database if it doesn't exist already'''
    if module_type_model := session.scalar(select(ShipModuleTypeModel).where(ShipModuleTypeModel.symbol == module.symbol)):
        return module_type_model
    module_type_model = ShipModuleTypeModel(
        module.symbol,
        module.name,
        module.description,
        module.capacity,
        module.range,
        RequirementsModel(module.requirements.power,
                          module.requirements.crew,
                          module.requirements.slots))
    session.add(module_type_model)
    return module_type_model


def __get_fuel_consumption(fuel_consumption: ShipFuel.ShipFuelConsumptionEvent, session: Session) -> ShipFuelConsumptionEventModel:
    if fcem := session.scalar(select(
            ShipFuelConsumptionEventModel).where(
            ShipFuelConsumptionEventModel.timestamp == fuel_consumption.timestamp)):
        return fcem
    fcem = ShipFuelConsumptionEventModel(fuel_consumption.amount,
                                         fuel_consumption.timestamp
                                         )
    return fcem


def __get_ship_cargo_item(item: ShipCargoItem, session: Session) -> ShipCargoItemModel:
    return ShipCargoItemModel(_get_or_create_good(item, session), item.units)


def _registration_to_schema(model: ShipRegistrationModel) -> ShipRegistration:
    return ShipRegistration(name=model.name,
                            factionSymbol=model.faction_symbol,
                            role=model.role)


def _route_to_schema(model: ShipNavRouteModel) -> ShipNavRoute:
    return ShipNavRoute(destination=_waypoint_to_schema(model.destination),
                        origin=_waypoint_to_schema(model.origin),
                        departureTime=model.departure_time.replace(tzinfo=UTC),
                        arrival=model.arrival.replace(tzinfo=UTC))


def _nav_to_schema(model: ShipNavModel) -> ShipNav:
    return ShipNav(systemSymbol=model.systemSymbol,
                   waypointSymbol=model.waypointSymbol,
                   status=model.status,
                   flightMode=model.flightMode,
                   route=_route_to_schema(model.route))


def _fuel_to_schema(model: ShipFuelModel) -> ShipFuel:
    return ShipFuel(current=model.current,
                    capacity=model.capacity,
                    consumed=ShipFuel.ShipFuelConsumptionEvent(amount=model.consumed.amount,
                                                               timestamp=model.consumed.timestamp.replace(tzinfo=UTC)))


def _cargo_to_schema(model: ShipCargoModel) -> ShipCargo:
    return ShipCargo(capacity=model.capacity,
                     units=model.units,
                     inventory=[ShipCargoItem(symbol=item.good.symbol,
                                              name=item.good.name,
                                              description=item.good.description,
                                              units=item.units) for item in model.inventory])


def _requirements_to_schema(model: RequirementsModel) -> ShipRequirements:
    return ShipRequirements(power=model.power, crew=model.crew, slots=model.slots)


def _frame_to_schema(model: ShipFrameModel) -> ShipFrame:
    return ShipFrame(symbol=model.frame_symbol,
                     name=model.frame_type.name,
                     description=model.frame_type.description,
                     condition=model.condition,
                     integrity=model.integrity,
                     requirements=_requirements_to_schema(
                         model.frame_type.requirements),
                     moduleSlots=model.frame_type.module_slots,
                     mountingPoints=model.frame_type.mounting_points,
                     fuelCapacity=model.frame_type.fuel_capacity)


def _reactor_to_schema(model: ShipReactorModel) -> ShipReactor:
    return ShipReactor(symbol=model.reactor_symbol,
                       name=model.reactor_type.name,
                       description=model.reactor_type.description,
                       condition=model.condition,
                       integrity=model.integrity,
                       requirements=_requirements_to_schema(
                           model.reactor_type.requirements),
                       powerOutput=model.reactor_type.power_output)


def _engine_to_schema(model: ShipEngineModel) -> ShipEngine:
    return ShipEngine(symbol=model.engine_symbol,
                      name=model.engine_type.name,
                      description=model.engine_type.description,
                      condition=model.condition,
                      integrity=model.integrity,
                      requirements=_requirements_to_schema(
                          model.engine_type.requirements),
                      speed=model.engine_type.speed)


def _mount_to_schema(model: ShipMountTypeModel) -> ShipMount:
    return ShipMount(symbol=model.symbol,
                     name=model.name,
                     description=model.description,
                     strength=model.strength,
                     deposits=[TradeSymbol(x.symbol) for x in model.deposits],
                     requirements=_requirements_to_schema(
                         model.requirements))


def _module_to_schema(model: ShipModuleTypeModel) -> ShipModule:
    return ShipModule(symbol=model.symbol,
                      name=model.name,
                      description=model.description,
                      capacity=model.capacity,
                      range=model.range,
                      requirements=_requirements_to_schema(
                          model.requirements))


def _crew_to_schema(model: ShipCrewModel) -> ShipCrew:
    return ShipCrew(current=model.current,
                    required=model.required,
                    capacity=model.capacity,
                    rotation=Rotation(model.rotation),
                    morale=model.morale,
                    wages=model.wages)


def _ship_to_schema(model: ShipModel) -> Ship:
    return Ship(symbol=model.symbol,
                registration=_registration_to_schema(model.registration),
                nav=_nav_to_schema(model.nav),
                fuel=_fuel_to_schema(model.fuel),
                cooldown=Cooldown(shipSymbol=model.symbol,
                                  totalSeconds=model.cooldown.total_seconds,
                                  remainingSeconds=time_until(
                                      model.cooldown.expiration.replace(tzinfo=UTC)),
                                  expiration=model.cooldown.expiration.replace(tzinfo=UTC)),
                cargo=_cargo_to_schema(model.cargo),
                frame=_frame_to_schema(model.frame),
                reactor=_reactor_to_schema(model.reactor),
                engine=_engine_to_schema(model.engine),
                mounts=[_mount_to_schema(mount) for mount in model.mounts],
                modules=[_module_to_schema(module)
                         for module in model.modules],
                crew=_crew_to_schema(model.crew))


def create_or_update_ship(ship: Ship):
    with Session(engine) as session:
        if model := __get_ship_from_db(ship.symbol, session):
            __update_ship(model, ship, session)
            return
        __create_ship(ship, session)


def update_ship(ship: Ship):
    with Session(engine) as session:
        if model := __get_ship_from_db(ship.symbol, session):
            __update_ship(model, ship, session)


def get_ship(symbol: str) -> Ship:
    with Session(engine) as session:
        if model := __get_ship_from_db(symbol, session):
            return _ship_to_schema(model)
        return None


# def get_ships() -> List[Ship]:
#     with Session(engine) as session:
#         return [_ship_to_schema(model) for model in session.scalars(select(ShipModel))]
