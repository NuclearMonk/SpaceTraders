from typing import List, Optional
from pydantic import ValidationError

from login import SYSTEM_BASE_URL, engine, get
from sqlalchemy.orm import Session
from models.waypoint import TraitModel, WaypointModel


def get_waypoint_with_symbol(symbol: str):
    if wp := _get_waypoint(symbol):
        print(f"from cache {symbol}")
        return wp
    else:
        print(f"getting fresh {symbol}")
        wp = _get_waypoint_with_symbol(symbol)
        print(wp)
        _store_waypoint(wp)
        return wp


def _get_waypoint_with_symbol(symbol: str) -> Optional["Waypoint"]:
    split_symbol = symbol.split("-")
    system_symbol = f"{split_symbol[0]}-{split_symbol[1]}"
    response = get(f"{SYSTEM_BASE_URL}/{system_symbol}/waypoints/{symbol}")
    if response.ok:
        js = response.json()
        try:
            return Waypoint.model_validate(js["data"])
        except ValidationError as e:
            print(e)
            return None
    print(response)
    return None


def _store_waypoint(wp: "Waypoint"):
    added_wp = WaypointModel()
    added_wp.symbol = wp.symbol
    added_wp.wp_type = wp.type
    added_wp.systemSymbol = wp.systemSymbol
    added_wp.x = wp.x
    added_wp.y = wp.y
    added_wp.parent_symbol = wp.orbits
    added_wp.faction = wp.faction.symbol
    for trait in wp.traits:
        added_wp.traits.append(store_trait(trait))
    for modifier in wp.modifiers:
        added_wp.modifiers.append(store_modifier(modifier))
    with Session(engine) as session:
        session.add(added_wp)
        session.commit()


def _record_to_schema(wp: WaypointModel) -> "Waypoint":
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


def get_waypoints_in_system(system_symbol: str, trait_symbol: Optional[str] = None) -> List["Waypoint"]:
    with Session(engine) as session:
        if trait_symbol:
            print(trait_symbol)
            return [_record_to_schema(t) for t in session.query(WaypointModel).filter(
                WaypointModel.systemSymbol == system_symbol,
                WaypointModel.traits.any(TraitModel.symbol == trait_symbol))]
        return [_record_to_schema(t) for t in session.query(WaypointModel).filter(
            WaypointModel.systemSymbol == system_symbol)]


def _get_waypoint(symbol: str):
    with Session(engine) as session:
        return _record_to_schema(session.query(WaypointModel).filter(WaypointModel.symbol == symbol).first())


from crud.modifiers import get_modifier, store_modifier
from schemas.navigation import Waypoint, WaypointFaction
from crud.traits import get_trait, store_trait