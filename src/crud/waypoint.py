
from datetime import timedelta
import logging
from typing import List
from sqlalchemy import select
from login import engine
from sqlalchemy.orm import Session
from models.waypoint import TraitModel, WaypointModel
from utils.utils import utcnow

from schemas.navigation import Waypoint, WaypointFaction, WaypointTraitSymbol, WaypointType
from .modifiers import _modifier_to_schema, _store_modifier
from .traits import _store_trait, _trait_to_schema
from logging import getLogger

STALE_TIME = timedelta(minutes=1)

logger = getLogger(__name__)


def get_waypoint_with_symbol(symbol: str):
    with Session(engine) as session:
        return _waypoint_to_schema(_get_waypoint(symbol, session))


def _get_waypoint(symbol: str, session: Session):
    logger.debug(f'Getting waypoint with symbol {symbol}')
    if wp := _get_waypoint_from_db(symbol, session):
        return wp
    return None


def create_update_waypoint(wp: Waypoint) -> Waypoint:
    with Session(engine) as session:
        if db_wp := _get_waypoint_from_db(wp.symbol, session):
            return _waypoint_to_schema(_update_waypoint_in_db(db_wp, wp, session))
        return _waypoint_to_schema(__store_waypoint_in_db(wp, session))


def refresh_system_cache(system_symbol: str) -> None:
    get_waypoints(system_symbol=system_symbol)


def _update_waypoint_in_db(db_wp: WaypointModel, wp: Waypoint, session: Session) -> WaypointModel:
    if wp.type:
        db_wp.wp_type = wp.type
    if wp.system_symbol:
        db_wp.system_symbol = wp.system_symbol
    if wp.x:
        db_wp.x = wp.x
    if wp.y:
        db_wp.y = wp.y
    if wp.orbits:
        db_wp.parent_symbol = wp.orbits
    if wp.faction:
        db_wp.faction = wp.faction.symbol
    if wp.traits is not None:
        db_wp.traits = [_store_trait(trait, session) for trait in wp.traits]
    if wp.modifiers is not None:
        db_wp.modifiers = [_store_modifier(modifier)
                           for modifier in wp.modifiers]
    db_wp.time_updated = utcnow()
    session.commit()
    return db_wp


def __store_waypoint_in_db(wp: Waypoint, session: Session) -> WaypointModel:
    added_wp = WaypointModel()
    added_wp.symbol = wp.symbol
    added_wp.wp_type = wp.type
    added_wp.system_symbol = wp.system_symbol
    added_wp.x = wp.x
    added_wp.y = wp.y
    added_wp.parent_symbol = wp.orbits
    added_wp.faction = wp.faction.symbol
    added_wp.traits = [_store_trait(trait, session) for trait in wp.traits]
    added_wp.modifiers = [_store_modifier(modifier, session)
                          for modifier in wp.modifiers]
    session.add(added_wp)
    session.commit()
    return added_wp


def _waypoint_to_schema(wp: WaypointModel) -> Waypoint:
    if not wp:
        return None
    return Waypoint(
        symbol=wp.symbol,
        type=wp.wp_type,
        x=wp.x,
        y=wp.y,
        orbits=wp.parent_symbol,
        orbitals=[_waypoint_to_schema(w) for w in wp.orbitals],
        traits=[_trait_to_schema(t) for t in wp.traits],
        modifiers=[_modifier_to_schema(m) for m in wp.modifiers],
        faction=WaypointFaction(symbol=wp.faction),
        isUnderConstruction=wp.isUnderConstruction
    )


def get_waypoints(system_symbol: str = None, type: WaypointType = None, trait_symbols: List[WaypointTraitSymbol] = None) -> List[Waypoint]:
    with Session(engine) as session:
        stmt = select(WaypointModel)
        if system_symbol:
            stmt = stmt.where(WaypointModel.system_symbol == system_symbol)
        if type:
            stmt = stmt.where(WaypointModel.wp_type == type)
        if trait_symbols:
            stmt = stmt.where(WaypointModel.traits.any(
                TraitModel.symbol.in_(trait_symbols)))
        return [get_waypoint_with_symbol(wp.symbol) for wp in session.scalars(stmt).all()]


def _get_waypoint_from_db(symbol: str, session):
    return session.scalars(select(WaypointModel).where(WaypointModel.symbol == symbol)).first()
