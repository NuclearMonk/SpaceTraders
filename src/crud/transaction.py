from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from login import engine
from models.market import MarketTransactionModel, TradeGoodModel
from schemas.market import Good, MarketTransaction



def get_transaction(ship_symbol :str , timestamp: datetime):
    with Session(engine) as session:
        return _record_to_schema(_get_transaction(ship_symbol,timestamp, session))

def store_transaction(trans: MarketTransaction):
    with Session(engine) as session:
        _store_transaction(trans,session)

def _store_transaction(trans: MarketTransaction, session)-> MarketTransactionModel:
    if t := _get_transaction(trans.shipSymbol, trans.timestamp, session):
        return t
    t = MarketTransactionModel()
    t.symbol=trans.waypointSymbol
    t.ship_symbol=trans.shipSymbol
    t.trade_symbol=trans.tradeSymbol
    t.type=trans.type_field
    t.units=trans.units
    t.price_per_unit=trans.pricePerUnit
    t.total_price=trans.totalPrice
    t.time_stamp=trans.timestamp
    session.add(t)
    session.commit()
    return t


def _record_to_schema(trans: MarketTransactionModel)-> MarketTransaction:
    if not trans:
        return None
    return MarketTransaction(
        waypointSymbol= trans.symbol,
        shipSymbol= trans.ship_symbol,
        tradeSymbol = trans.trade_symbol,
        type= trans.type,
        units = trans.units,
        pricePerUnit =trans.price_per_unit,
        totalPrice= trans.total_price,
        timestamp=  trans.time_stamp
    )



def _get_transaction(ship_symbol:str, timestamp: datetime, session: Session)-> MarketTransactionModel:
    return session.scalars(select(MarketTransactionModel).where(MarketTransactionModel.ship_symbol == ship_symbol, MarketTransactionModel.time_stamp == timestamp)).first()