

from sqlalchemy import select
from sqlalchemy.orm import Session
from crud.waypoint import _get_waypoint, _waypoint_to_schema
from models.system import SystemFactionModel, SystemModel
from schemas.navigation import System, WaypointFaction
from login import engine


def get_system_db(symbol: str) -> System:
    with Session(engine) as session:
        return _system_to_schema(_get_system(symbol, session))


def create_update_system_db(system: System) -> System:
    with Session(engine) as session:
        if model := _get_system(system.symbol,session):
            return _system_to_schema(_update_system(model, system, session))
        return _system_to_schema(_create_system(system, session))


def _system_to_schema(model: SystemModel) -> System:
    if not model:
        return None
    return System(symbol=model.symbol,
                  sectorSymbol=model.sector_symbol,
                  type=model.type,
                  x=model.x,
                  y=model.y,
                  waypoints=[_waypoint_to_schema(wp)
                             for wp in model.waypoints],
                  factions=[WaypointFaction(faction.faction_symbol) for faction in model.factions])


def _update_system(model: SystemModel, system: System, session: Session) -> SystemModel:
    model = [_get_waypoint(wp.symbol, session) for wp in system.waypoints],
    model = [SystemFactionModel(faction.symbol) for faction in system.factions]
    session.add(model)
    session.commit()
    return model


def _create_system(system: System, session: Session) -> SystemModel:
    model = SystemModel(system.symbol,
                        system.sectorSymbol,
                        system.type,
                        system.x,
                        system.y,
                        [_get_waypoint(wp.symbol, session)
                         for wp in system.waypoints],
                        [SystemFactionModel(faction.symbol) for faction in system.factions])
    session.add(model)
    session.commit()
    return model


def _get_system(symbol: str, session: Session) -> SystemModel:
    return session.scalar(select(SystemModel).where(SystemModel.symbol == symbol))
