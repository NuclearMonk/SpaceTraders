

from typing import List, Optional
from sqlalchemy import select
from crud.tradegood import _get_trade_good, _good_to_schema, _get_or_create_good
from crud.transaction import _transaction_to_schema, _get_create_transaction
from models.market import MarketModel, MarketTradeGoodModel
from models.waypoint import WaypointModel
from schemas.market import Market, MarketTradeGood, TradeSymbol
from sqlalchemy.orm import Session
from login import engine
from utils.utils import utcnow
from logging import getLogger

logger = getLogger(__name__)


def create_update_market(market: Market) -> Market:
    with Session(engine) as session:
        if model := _get_market_from_db(market.symbol, session):
            return _market_to_schema(_update_market_in_db(model, market, session))
        return _market_to_schema(_create_market_in_db(market, session))


def get_market_from_db(symbol: str) -> Optional[Market]:
    with Session(engine) as session:
        return _market_to_schema(_get_market_from_db(symbol, session))


def get_markets_in_system_db(system: str) -> List[Market]:
    stmt = select(MarketModel).join(WaypointModel).where(
        WaypointModel.system_symbol == system)
    with Session(engine) as session:
        return [_market_to_schema(x) for x in session.scalars(stmt)]


def get_markets_exporting_db(symbol: TradeSymbol) -> List[Market]:
    with Session(engine) as session:
        if good := _get_trade_good(symbol, session):
            return [_market_to_schema(m) for m in good.exporters]
        return []


def get_markets_importing_db(symbol: TradeSymbol) -> List[Market]:
    with Session(engine) as session:
        if good := _get_trade_good(symbol, session):
            return [_market_to_schema(m) for m in good.importers]
        return []


def get_markets_exchanging_db(symbol: TradeSymbol) -> List[Market]:
    with Session(engine) as session:
        if good := _get_trade_good(symbol, session):
            return [_market_to_schema(m) for m in good.exchangers]
        return []


def _market_to_schema(model: MarketModel) -> Market:
    if not model:
        return None
    return Market(
        symbol=model.symbol,
        exports=[_good_to_schema(good) for good in model.exports],
        imports=[_good_to_schema(good) for good in model.imports],
        exchange=[_good_to_schema(good) for good in model.exchanges],
        transactions=[_transaction_to_schema(
            trans) for trans in model.transactions],
        tradeGoods=[_market_trade_good_to_schema(
            trade_good) for trade_good in model.trade_goods],
        last_updated=model.time_updated_utc
    )


def _get_create_market_trade_good(market_trade_good: MarketTradeGood, session: Session) -> MarketTradeGoodModel:
    model = MarketTradeGoodModel(_get_trade_good(market_trade_good.symbol, session),
                                 market_trade_good.type,
                                 market_trade_good.tradeVolume,
                                 market_trade_good.supply,
                                 market_trade_good.activity,
                                 market_trade_good.purchasePrice,
                                 market_trade_good.sellPrice
                                 )
    return model


def _market_trade_good_to_schema(model: MarketTradeGoodModel) -> MarketTradeGood:
    return MarketTradeGood(symbol=model.good_symbol,
                           type=model.type,
                           tradeVolume=model.trade_volume,
                           supply=model.supply,
                           activity=model.activity,
                           purchasePrice=model.purchase_price,
                           sellPrice=model.sell_price)


def _create_market_in_db(market: Market, session: Session) -> MarketModel:
    model = MarketModel()
    model.symbol = market.symbol
    session.add(model)
    model.imports = [_get_or_create_good(
        good, session) for good in market.imports]
    model.exports = [_get_or_create_good(
        good, session) for good in market.exports]
    model.exchanges = [_get_or_create_good(good, session)
                       for good in market.exchange]
    session.commit()
    if market.transactions:
        print("adding_transactions")
        model.transactions = [_get_create_transaction(
            trans, session) for trans in market.transactions]
    if market.tradeGoods:
        model.trade_goods = [_get_create_market_trade_good(
            tg, session) for tg in market.tradeGoods]
    session.commit()
    return model


def _update_market_in_db(model: MarketModel, market: Market, session: Session) -> MarketModel:
    if market.transactions:
        print("adding_transactions")

        model.transactions.extend([_get_create_transaction(trans, session)
                                   for trans in market.transactions])
    if market.tradeGoods:
        model.trade_goods = [_get_create_market_trade_good(trade_good, session)
                             for trade_good in market.tradeGoods]
    model.time_updated = utcnow()
    session.commit()
    return model


def _get_market_from_db(symbol: str, session) -> Optional[MarketModel]:
    return session.scalar(select(MarketModel).where(MarketModel.symbol == symbol))
