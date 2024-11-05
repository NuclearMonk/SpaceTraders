from sqlalchemy import select
from sqlalchemy.orm import Session
from login import engine
from models.market import TradeGoodModel, TradeSymbolModel
from schemas.market import TradeGood, TradeSymbol


def get_good(symbol: TradeSymbol):
    with Session(engine) as session:
        return _good_to_schema(_get_trade_good(symbol, session))



def get_or_create_good(good: TradeGood) -> TradeGoodModel:
    with Session(engine) as session:
        return _get_or_create_good(good, session)


def _get_or_create_good(good: TradeGood, session: Session) -> TradeGoodModel:
    """gets a good from the database, if it doesn't exist, creates it """
    if g := _get_trade_good(good.symbol, session):
        return g
    g = TradeGoodModel()
    g.symbol = good.symbol
    g.name = good.name
    g.description = good.description
    session.add(g)
    session.commit()
    return g


def _good_to_schema(good: TradeGoodModel) -> TradeGood:
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
    return TradeSymbolModel(symbol)


def _get_trade_good(symbol: TradeSymbol, session: Session) -> TradeGoodModel:
    if model := session.scalar(select(TradeGoodModel).where(TradeGoodModel.symbol == symbol)):
        return model
    return None
