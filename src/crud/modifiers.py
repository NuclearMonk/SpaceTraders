from login import engine
from models.waypoint import ModifierModel
from schemas.navigation import WaypointModifier
from sqlalchemy.orm import Session

def get_modifier(symbol: str):
    return _record_to_schema(_get_modifier(symbol))


def store_modifier(trait: WaypointModifier, session: Session) -> ModifierModel:
    if t := _get_modifier(trait.symbol):
        return t
    t = ModifierModel()
    t.symbol = trait.symbol
    t.name = trait.name
    t.description = trait.description
    session.add(t)
    session.commit()
    return t


def _get_modifier(symbol: str):
    with Session(engine) as session:
        return session.query(ModifierModel).filter(ModifierModel.symbol == symbol).first()


def _record_to_schema(record: ModifierModel) -> WaypointModifier:
    if not record:
        return None
    return WaypointModifier(
        symbol=record.symbol,
        name=record.name,
        description=record.description
    )
