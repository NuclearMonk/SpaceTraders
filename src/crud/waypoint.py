
from datetime import UTC, timedelta
from typing import List, Optional
from pydantic import ValidationError
from sqlalchemy import select

from login import SYSTEM_BASE_URL, engine, get
from sqlalchemy.orm import Session
from models.waypoint import TraitModel, WaypointModel
from utils.utils import utcnow

from schemas.navigation import Waypoint, WaypointFaction
from crud import get_modifier, store_modifier, get_trait, store_trait
from logging import getLogger

STALE_TIME = timedelta(minutes=1)

logger = getLogger(__name__)


def get_waypoint_with_symbol(symbol: str):
    logger.debug(f"Getting waypoint with symbol {symbol}")
    with Session(engine) as session:
        if wp := _get_waypoint_from_db(symbol, session):
            if not utcnow() - wp.time_updated_utc < STALE_TIME:
                # we refresh under construction waypoints thing may have changed
                if wp.isUnderConstruction:
                    logger.debug("Waypoint is under construction. Refreshing")
                    fresh_wp = _get_waypoint_from_server(symbol)
                    return _record_to_schema(_update_waypoint_in_db(wp, fresh_wp, session))
                # modifiers can change so we check for those too
                if wp.modifiers:
                    logger.debug("Waypoint has TRAITS so refreshing")
                    fresh_wp = _get_waypoint_from_server(symbol)
                    return _record_to_schema(_update_waypoint_in_db(wp, fresh_wp, session))
                if "UNCHARTED" in {t.symbol for t in wp.traits}:
                    logger.debug("Waypoint is UNCHARTED so refreshing")
                    fresh_wp = _get_waypoint_from_server(symbol)
                    return _record_to_schema(_update_waypoint_in_db(wp, fresh_wp, session))
            logger.debug("CACHE IS FRESH")
            return _record_to_schema(wp)
        logger.debug("ADDED NEW CACHE ROW")
        fresh_wp = _get_waypoint_from_server(symbol)
        wp = _record_to_schema(_store_waypoint_in_db(fresh_wp, session))
        return wp


def update_waypoint_cache(wp: Waypoint) -> Waypoint:
    with Session(engine) as session:
        if db_wp := _get_waypoint_from_db(wp.symbol, session):
            return _record_to_schema(_update_waypoint_in_db(db_wp, wp, session))
        fresh_wp = _get_waypoint_from_server(wp.symbol)
        wp = _record_to_schema(_store_waypoint_in_db(fresh_wp, session))
        return wp


def refresh_system_cache(system_symbol: str) -> None:
    get_waypoints(system_symbol=system_symbol)


def _get_waypoint_from_server(symbol: str) -> Optional[Waypoint]:
    split_symbol = symbol.split("-")
    system_symbol = f"{split_symbol[0]}-{split_symbol[1]}"
    response = get(f"{SYSTEM_BASE_URL}/{system_symbol}/waypoints/{symbol}")
    if response.ok:
        js = response.json()
        try:
            return Waypoint.model_validate(js["data"])
        except ValidationError as e:
            logger.warning(e)
            return None
    logger.debug(response)
    return None


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
        db_wp.traits = [store_trait(trait, session) for trait in wp.traits]
    if wp.modifiers is not None:
        db_wp.modifiers = [store_modifier(modifier)
                           for modifier in wp.modifiers]
    db_wp.time_updated = utcnow()
    session.commit()
    return db_wp


def _store_waypoint_in_db(wp: Waypoint, session: Session) -> WaypointModel:
    added_wp = WaypointModel()
    added_wp.symbol = wp.symbol
    added_wp.wp_type = wp.type
    added_wp.system_symbol = wp.system_symbol
    added_wp.x = wp.x
    added_wp.y = wp.y
    added_wp.parent_symbol = wp.orbits
    added_wp.faction = wp.faction.symbol
    added_wp.traits = [store_trait(trait, session) for trait in wp.traits]
    added_wp.modifiers = [store_modifier(modifier, session)
                          for modifier in wp.modifiers]
    session.add(added_wp)
    session.commit()
    return added_wp


def _record_to_schema(wp: WaypointModel) -> Waypoint:
    if not wp:
        return None
    return Waypoint(
        symbol=wp.symbol,
        type=wp.wp_type,
        x=wp.x,
        y=wp.y,
        orbits=wp.parent_symbol,
        orbitals=[_record_to_schema(w) for w in wp.orbitals],
        traits=[get_trait(t.symbol) for t in wp.traits],
        modifiers=[get_modifier(m.symbol) for m in wp.modifiers],
        faction=WaypointFaction(symbol=wp.faction),
        isUnderConstruction=wp.isUnderConstruction
    )


def get_waypoints(system_symbol: str = None, type: str = None, trait_symbols: List[str] = None) -> List[Waypoint]:
    with Session(engine) as session:
        stmt = select(WaypointModel)
        if system_symbol:
            stmt = stmt.where(WaypointModel.system_symbol == system_symbol)
        if type:
            stmt = stmt.where(WaypointModel.wp_type == type)
        if trait_symbols:
            stmt = stmt.where(WaypointModel.traits.any(TraitModel.symbol.in_(trait_symbols)))
        return [get_waypoint_with_symbol(wp.symbol) for wp in session.scalars(stmt).all()]


def _get_waypoint_from_db(symbol: str, session):
    return session.scalars(select(WaypointModel).where(WaypointModel.symbol == symbol)).first()
