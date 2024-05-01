from sqlalchemy import select
from sqlalchemy.orm import Session
from login import engine
from models.market import TradeGoodModel
from schemas.market import Good


def get_good(symbol: str):
    with Session(engine) as session:
        return _record_to_schema(_get_trade_good(symbol, session))


def get_good_model(good: Good, session) -> TradeGoodModel:
    if g := _get_trade_good(good.symbol, session):
        return g
    g = TradeGoodModel()
    g.symbol = good.symbol
    g.name = good.name
    g.description = good.description
    return g


def store_good(good: Good) -> TradeGoodModel:
    with Session(engine) as session:
        if g := _get_trade_good(good.symbol, session):
            return g
        g = TradeGoodModel()
        g.symbol = good.symbol
        g.name = good.name
        g.description = good.description
        session.add(g)
        session.commit()
        return g


def _record_to_schema(good: TradeGoodModel) -> Good:
    if not good:
        return None
    return Good(
        symbol=good.symbol,
        name=good.name,
        description=good.description
    )


def _get_trade_good(symbol: str, session: Session) -> TradeGoodModel:
    return session.scalars(select(TradeGoodModel).where(TradeGoodModel.symbol == symbol)).first()
