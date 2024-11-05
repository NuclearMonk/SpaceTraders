from datetime import UTC, datetime
from typing import Any, List, Optional
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.waypoint import WaypointModel
from schemas.market import ActivityLevel, MarketTradeGoodType, SupplyLevel, TradeSymbol, TransactionType
from utils.utils import utcnow
from . import Base


market_exports = Table(
    'market_exports',
    Base.metadata,
    Column('market_symbol', ForeignKey('markets.symbol'),
           primary_key=True, type_=Text(20)),
    Column('good_symbol', ForeignKey('trade_goods.symbol'),
           primary_key=True, type_=Text(20)),
)
market_imports = Table(
    'market_imports',
    Base.metadata,
    Column('market_symbol', ForeignKey('markets.symbol'),
           primary_key=True, type_=Text(20)),
    Column('good_symbol', ForeignKey('trade_goods.symbol'),
           primary_key=True, type_=Text(20)),
)

market_exchanges = Table(
    'market_exchanges',
    Base.metadata,
    Column('market_symbol', ForeignKey('markets.symbol'),
           primary_key=True, type_=Text(20)),
    Column('good_symbol', ForeignKey('trade_goods.symbol'),
           primary_key=True, type_=Text(20)),
)


class TradeSymbolModel(Base):
    __tablename__ = 'trade_symbols'
    symbol: Mapped[TradeSymbol] = mapped_column(
        Enum(TradeSymbol), primary_key=True)
    good: Mapped['TradeGoodModel'] = relationship()

    def __init__(self, symbol: TradeSymbol, **kw: Any):
        super().__init__(**kw)
        self.symbol = symbol


class TradeGoodModel(Base):
    __tablename__ = 'trade_goods'
    symbol: Mapped[TradeSymbol] = mapped_column(
        ForeignKey(TradeSymbolModel.symbol), primary_key=True)
    name: Mapped[str] = mapped_column(Text(30))
    description: Mapped[str] = mapped_column(Text(500))
    exporters: Mapped[List['MarketModel']] = relationship(
        secondary=market_exports, back_populates='exports')
    importers: Mapped[List['MarketModel']] = relationship(
        secondary=market_imports, back_populates='imports')
    exchangers: Mapped[List['MarketModel']] = relationship(
        secondary=market_exchanges, back_populates='exchanges')
    trades: Mapped[List['MarketTransactionModel']] = relationship(
        back_populates='trade_good')


class MarketModel(Base):
    __tablename__ = 'markets'
    symbol: Mapped[str] = mapped_column(
        Text(20), ForeignKey(WaypointModel.symbol), primary_key=True)
    waypoint: Mapped[WaypointModel] = relationship()
    exports: Mapped[List[TradeGoodModel]] = relationship(
        secondary=market_exports, back_populates='exporters')
    imports: Mapped[List[TradeGoodModel]] = relationship(
        secondary=market_imports, back_populates='importers')
    exchanges: Mapped[List[TradeGoodModel]] = relationship(
        secondary=market_exchanges, back_populates='exchangers')
    transactions: Mapped[List['MarketTransactionModel']
                         ] = relationship(back_populates='market', uselist=True)
    trade_goods: Mapped[List['MarketTradeGoodModel']
                        ] = relationship(back_populates='market', uselist=True, cascade='save-update, merge, delete, delete-orphan')

    time_updated = Column(DateTime(timezone=False),
                          default=utcnow, onupdate=utcnow)

    @property
    def time_updated_utc(self) -> datetime:
        return self.time_updated.replace(tzinfo=UTC)


class MarketTransactionModel(Base):
    __tablename__ = 'market_transactions'
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    ship_symbol = mapped_column(Text(20))
    time_stamp: Mapped[datetime] = mapped_column(DateTime(False))
    symbol: Mapped[str] = mapped_column(
        Text(20), ForeignKey(MarketModel.symbol))
    market: Mapped[MarketModel] = relationship(back_populates='transactions')
    trade_symbol: Mapped[str] = mapped_column(
        Text(20), ForeignKey('trade_goods.symbol'))
    trade_good: Mapped[TradeGoodModel] = relationship(back_populates='trades')
    type: Mapped[TransactionType] = mapped_column(Enum(TransactionType))
    units: Mapped[Integer] = mapped_column(Integer)
    price_per_unit: Mapped[Integer] = mapped_column(Integer)
    total_price: Mapped[Integer] = mapped_column(Integer)


class MarketTradeGoodModel(Base):
    __tablename__ = 'market_trade_goods'
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    market_symbol: Mapped[str] = mapped_column(
        Text(20), ForeignKey(MarketModel.symbol))
    good_symbol:  Mapped[TradeSymbol] = mapped_column(
        Enum(TradeSymbol), ForeignKey(TradeGoodModel.symbol))
    type:  Mapped[MarketTradeGoodType] = mapped_column(
        Enum(MarketTradeGoodType))
    market: Mapped[MarketModel] = relationship(back_populates="trade_goods")
    good: Mapped[TradeGoodModel] = relationship()
    trade_volume: Mapped[Integer] = mapped_column(Integer)
    supply: Mapped[SupplyLevel] = mapped_column(Enum(SupplyLevel))
    activity: Mapped[Optional[ActivityLevel]
                     ] = mapped_column(Enum(ActivityLevel))
    purchase_price: Mapped[Integer] = mapped_column(Integer)
    sell_price: Mapped[Integer] = mapped_column(Integer)
    time_stamp: Mapped[DateTime] = Column(DateTime(False), default=utcnow)

    def __init__(self,
                 good: TradeGoodModel,
                 type: MarketTradeGoodType,
                 trade_volume: int,
                 supply: SupplyLevel,
                 activity: ActivityLevel,
                 purchase_price: int,
                 sell_price: int, **kw: Any):
        super().__init__(**kw)
        self.good = good
        self.type = type
        self.trade_volume = trade_volume
        self.supply = supply
        self.activity = activity
        self.purchase_price = purchase_price
        self.sell_price = sell_price
