from login import engine
from schemas.navigation import Waypoint, WaypointFaction, get_waypoint_with_symbol
from sqlalchemy.orm import Session
from models.waypoint import WaypointModel

def get_waypoint(symbol: str):
    if wp:=_get_waypoint(symbol):
        print(f"from cache {symbol}")
        return wp
    else:
        print(f"getting fresh {symbol}")
        wp = get_waypoint_with_symbol(symbol)
        print(wp)
        _store_waypoint(wp)
        return wp

def _store_waypoint(wp: Waypoint):
    added_wp = WaypointModel()
    added_wp.symbol = wp.symbol
    added_wp.wp_type = wp.type
    added_wp.systemSymbol = wp.systemSymbol
    added_wp.x = wp.x
    added_wp.y = wp.y
    added_wp.parent_symbol = wp.orbits
    added_wp.faction = wp.faction.symbol
    with Session(engine) as session:
        session.add(added_wp)
        session.commit()

def _record_to_schema(wp: WaypointModel)-> Waypoint:
    if not wp:
        return None
    return Waypoint(
        symbol = wp.symbol,
        type = wp.wp_type,
        x= wp.x,
        y= wp.y,
        orbits= wp.parent_symbol,
        orbitals = [_record_to_schema(w) for w in wp.orbitals],
        faction= WaypointFaction(symbol=wp.faction),
        isUnderConstruction=wp.isUnderConstruction
    )

def _get_waypoint(symbol: str):
    with Session(engine) as session:
        return _record_to_schema(session.query(WaypointModel).filter(WaypointModel.symbol == symbol).first())