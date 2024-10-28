from sqlalchemy import select
from sqlalchemy.orm import Session
from login import engine
from models.market import TradeGoodModel, TradeSymbolModel
from schemas.market import TradeGood, TradeSymbol


def get_good(symbol: str):
    with Session(engine) as session:
        return _record_to_schema(_get_trade_good(symbol, session))


def get_good_model(good: TradeGood, session) -> TradeGoodModel:
    if g := _get_trade_good(good.symbol, session):
        return g
    g = TradeGoodModel()
    g.symbol = good.symbol
    g.name = good.name
    g.description = good.description
    return g


def store_good(good: TradeGood) -> TradeGoodModel:
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


def _record_to_schema(good: TradeGoodModel) -> TradeGood:
    if not good:
        return None
    return TradeGood(
        symbol=good.symbol,
        name=good.name,
        description=good.description
    )


def _get_trade_symbol_model(symbol: TradeSymbol, session: Session) -> TradeSymbolModel:
    if model := session.scalar(select(TradeSymbolModel).where(TradeSymbolModel.symbol == symbol)):
        return model
    model = TradeSymbolModel()
    model.symbol = symbol
    return model


def _get_trade_good(symbol: str, session: Session) -> TradeGoodModel:
    return session.scalar(select(TradeGoodModel).where(TradeGoodModel.symbol == symbol))
