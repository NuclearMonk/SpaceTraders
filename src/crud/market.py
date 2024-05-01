

from datetime import UTC, timedelta
from typing import List, Optional
from sqlalchemy import select
from crud.tradegood import get_good, get_good_model
from crud.transaction import get_transaction, store_transaction
from crud.waypoint import get_waypoint_with_symbol, get_waypoints_in_system
from models.market import MarketModel
from schemas.market import Market
from sqlalchemy.orm import Session
from login import HEADERS, SYSTEM_BASE_URL, engine, get
from schemas.navigation import System
from utils.utils import system_symbol_from_wp_symbol, utcnow
STALE_TIME = timedelta(minutes=1)


def get_market_with_symbol(symbol: str):
    with Session(engine) as session:
        if market := _get_market_from_db(symbol, session):
            if utcnow() - market.time_updated_utc < STALE_TIME:
                print("fresh from cache")
                return _record_to_schema(market)
            else:
                print("updating cache")
                fresh_market = _get_market_from_server(symbol)
                return _record_to_schema(_update_market_in_db(market, fresh_market, session))
        print("added new cache row")
        fresh_market = _get_market_from_server(symbol)
        market = _record_to_schema(_store_market_in_db(fresh_market, session))
        return market


def get_all_markets(system: System) -> List[Market]:
    market_waypoints = get_waypoints_in_system(system.symbol, "MARKETPLACE")
    markets = [get_market_with_symbol(waypoint.symbol)
               for waypoint in market_waypoints]
    return markets


def _record_to_schema(market: MarketModel) -> Market:
    if not market:
        return None
    return Market(
        symbol=market.symbol,
        exports=[get_good(good.symbol) for good in market.exports],
        imports=[get_good(good.symbol) for good in market.imports],
        exchange=[get_good(good.symbol) for good in market.exchanges],
        transactions=[get_transaction(trans.ship_symbol, trans.time_stamp) for trans in market.transactions if trans]
    )


def _store_market_in_db(market: Market, session: Session) -> MarketModel:
    new_market = MarketModel()
    new_market.symbol = market.symbol
    session.add(new_market)
    new_market.imports = [get_good_model(good, session) for good in market.imports]
    new_market.exports = [get_good_model(good, session) for good in market.exports]
    new_market.exchanges = [get_good_model(good, session)
                            for good in market.exchange]
    if market.transactions:
        new_market.transactions = [store_transaction(
            trans, session) for trans in market.transactions]
    else:
        new_market.transactions= []
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
