from login import engine
from models.waypoint import TraitModel
from schemas.navigation import WaypointTrait
from sqlalchemy.orm import Session


def get_trait(symbol: str):
    return _record_to_schema(_get_trait(symbol))


def store_trait(trait: WaypointTrait) -> TraitModel:
    if t := _get_trait(trait.symbol):
        return t
    t = TraitModel()
    t.symbol = trait.symbol
    t.name = trait.name
    t.description = trait.description
    with Session(engine) as session:
        session.add(t)
        session.commit()
        return t


def _get_trait(symbol: str):
    with Session(engine) as session:
        return session.query(TraitModel).filter(TraitModel.symbol == symbol).first()


def _record_to_schema(record: TraitModel) -> WaypointTrait:
    if not record:
        return None
    return WaypointTrait(
        symbol=record.symbol,
        name=record.name,
        description=record.description
    )
