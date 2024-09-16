

from datetime import timedelta
from typing import List, Optional
from sqlalchemy import select
from crud.tradegood import get_good, get_good_model
from crud.transaction import get_transaction, store_transaction
from models.market import MarketModel, TradeGoodModel
from models.waypoint import WaypointModel
from schemas.market import Market
from sqlalchemy.orm import Session
from login import HEADERS, SYSTEM_BASE_URL, engine, get
from utils.utils import system_symbol_from_wp_symbol, utcnow
from logging import getLogger
logger = getLogger(__name__)
STALE_TIME = timedelta(minutes=1)


def get_market_with_symbol(symbol: str):
    logger.info(f"getting market with symbol {symbol}")
    with Session(engine) as session:
        if market := _get_market_from_db(symbol, session):
            if utcnow() - market.time_updated_utc < STALE_TIME:
                logger.info("fresh from cache")
                return _record_to_schema(market)
            else:
                logger.info("updating cache")
                
                fresh_market = _get_market_from_server(symbol)
                return _record_to_schema(_update_market_in_db(market, fresh_market, session))
        logger.info("fresh from cache")
        fresh_market = _get_market_from_server(symbol)
        market = _record_to_schema(_store_market_in_db(fresh_market, session))
        return market


def get_markets_in_system(system: str) -> List[Market]:
    stmt = select(MarketModel).join(WaypointModel).where(
        WaypointModel.systemSymbol == system)
    with Session(engine) as session:
        return [_record_to_schema(x) for x in session.scalars(stmt)]


def get_markets_exporting(good: str, system: Optional[str] = None) -> List[Market]:
    if system:
        stmt = select(MarketModel).join(WaypointModel).where(
            WaypointModel.systemSymbol == system,
            MarketModel.exports.any(TradeGoodModel.symbol == good))
    else:
        stmt = select(MarketModel).where(
            MarketModel.exports.any(TradeGoodModel.symbol == good))
    with Session(engine) as session:
        return [_record_to_schema(x) for x in session.scalars(stmt)]


def get_markets_importing(good: str, system: Optional[str] = None) -> List[Market]:
    if system:
        stmt = select(MarketModel).join(WaypointModel).where(
            WaypointModel.systemSymbol == system,
            MarketModel.imports.any(TradeGoodModel.symbol == good))
    else:
        stmt = select(MarketModel).where(
            MarketModel.imports.any(TradeGoodModel.symbol == good))
    with Session(engine) as session:
        return [_record_to_schema(x) for x in session.scalars(stmt)]


def get_markets_exchanging(good: str, system: Optional[str] = None) -> List[Market]:
    if system:
        stmt = select(MarketModel).join(WaypointModel).where(
            WaypointModel.systemSymbol == system,
            MarketModel.exchanges.any(TradeGoodModel.symbol == good))
    else:
        stmt = select(MarketModel).where(
            MarketModel.exchanges.any(TradeGoodModel.symbol == good))
    with Session(engine) as session:
        return [_record_to_schema(x) for x in session.scalars(stmt)]


def _record_to_schema(market: MarketModel) -> Market:
    if not market:
        return None
    return Market(
        symbol=market.symbol,
        exports=[get_good(good.symbol) for good in market.exports],
        imports=[get_good(good.symbol) for good in market.imports],
        exchange=[get_good(good.symbol) for good in market.exchanges],
        transactions=[get_transaction(
            trans.ship_symbol, trans.time_stamp) for trans in market.transactions if trans]
    )


def _store_market_in_db(market: Market, session: Session) -> MarketModel:
    new_market = MarketModel()
    new_market.symbol = market.symbol
    session.add(new_market)
    new_market.imports = [get_good_model(
        good, session) for good in market.imports]
    new_market.exports = [get_good_model(
        good, session) for good in market.exports]
    new_market.exchanges = [get_good_model(good, session)
                            for good in market.exchange]
    if market.transactions:
        new_market.transactions = [store_transaction(
            trans, session) for trans in market.transactions]
    else:
        new_market.transactions = []
    session.commit()
    return new_market


def _update_market_in_db(db_market: MarketModel, market: Market, session: Session) -> MarketModel:
    if market.transactions:
        db_market.transactions = [store_transaction(trans, session)
                                  for trans in market.transactions]
    db_market.time_updated = utcnow()
    session.commit()
    return db_market


def _get_market_from_server(symbol: str) -> Optional[Market]:
    response = get(f"{SYSTEM_BASE_URL}/{system_symbol_from_wp_symbol(symbol)
                                        }/waypoints/{symbol}/market", headers=HEADERS)
    if response.ok:
        js = response.json()
        return Market.model_validate(js["data"])
    else:
        return None


def _get_market_from_db(symbol: str, session):
    return session.scalars(select(MarketModel).where(MarketModel.symbol == symbol)).first()
