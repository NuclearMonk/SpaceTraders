from sqlalchemy import select
from login import engine
from models.waypoint import TraitModel
from schemas.navigation import WaypointTrait
from sqlalchemy.orm import Session


def _get_trait(symbol: str):
    with Session(engine) as session:
        return _trait_to_schema(_get_trait(symbol, session))


def _store_trait(trait: WaypointTrait, session: Session) -> TraitModel:
    if t := _get_trait(trait.symbol, session):
        return t
    t = TraitModel()
    t.symbol = trait.symbol
    t.name = trait.name
    t.description = trait.description
    session.add(t)
    session.commit()
    return t


def _get_trait(symbol: str, session: Session):
    return session.scalars(select(TraitModel).where(TraitModel.symbol == symbol)).first()


def _trait_to_schema(record: TraitModel) -> WaypointTrait:
    if not record:
        return None
    return WaypointTrait(
        symbol=record.symbol,
        name=record.name,
        description=record.description
    )
