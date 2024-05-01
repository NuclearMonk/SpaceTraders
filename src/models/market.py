from datetime import UTC
from typing import List, Optional
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.waypoint import WaypointModel
from utils.utils import utcnow
from . import Base


market_exports = Table(
    "market_exports",
    Base.metadata,
    Column("market_symbol", ForeignKey("markets.symbol"),
           primary_key=True, type_=Text(20)),
    Column("good_symbol", ForeignKey("trade_goods.symbol"),
           primary_key=True, type_=Text(20)),
)
market_imports = Table(
    "market_imports",
    Base.metadata,
    Column("market_symbol", ForeignKey("markets.symbol"),
           primary_key=True, type_=Text(20)),
    Column("good_symbol", ForeignKey("trade_goods.symbol"),
           primary_key=True, type_=Text(20)),
)

market_exchanges = Table(
    "market_exchanges",
    Base.metadata,
    Column("market_symbol", ForeignKey("markets.symbol"),
           primary_key=True, type_=Text(20)),
    Column("good_symbol", ForeignKey("trade_goods.symbol"),
           primary_key=True, type_=Text(20)),
)


class TradeGoodModel(Base):
    __tablename__ = "trade_goods"
    symbol: Mapped[str] = mapped_column(Text(20), primary_key=True)
    name: Mapped[str] = mapped_column(Text(30))
    description: Mapped[str] = mapped_column(Text(500))
    exporters: Mapped[List["MarketModel"]] = relationship(
        secondary=market_exports, back_populates="exports")
    importers: Mapped[List["MarketModel"]] = relationship(
        secondary=market_imports, back_populates="imports")
    exchangers: Mapped[List["MarketModel"]] = relationship(
        secondary=market_exchanges, back_populates="exchanges")
    trades: Mapped[List["MarketTransactionModel"]] = relationship(
        back_populates="trade_good")


class MarketModel(Base):
    __tablename__ = "markets"
    symbol: Mapped[str] = mapped_column(
        Text(20), ForeignKey(WaypointModel.symbol), primary_key=True)
    waypoint: Mapped[WaypointModel] = relationship()
    exports: Mapped[List[TradeGoodModel]] = relationship(
        secondary=market_exports, back_populates="exporters")
    imports: Mapped[List[TradeGoodModel]] = relationship(
        secondary=market_imports, back_populates="importers")
    exchanges: Mapped[List[TradeGoodModel]] = relationship(
        secondary=market_exchanges, back_populates="exchangers")
    transactions: Mapped[List["MarketTransactionModel"]] = relationship(back_populates="market")
    time_updated = Column(DateTime(timezone=False),
                        default=utcnow, onupdate=utcnow)

    @property
    def time_updated_utc(self):
        return self.time_updated.replace(tzinfo=UTC)


class MarketTransactionModel(Base):
    __tablename__ = "market_transactions"
    ship_symbol = mapped_column(Text(20), primary_key=True)
    time_stamp: Mapped[DateTime] = mapped_column(DateTime(timezone=False), primary_key=True)
    symbol: Mapped[str] = mapped_column(
        Text(20), ForeignKey(MarketModel.symbol))
    market: Mapped[MarketModel] = relationship(back_populates="transactions")
    trade_symbol: Mapped[str] = mapped_column(
        Text(20), ForeignKey("trade_goods.symbol"))
    trade_good: Mapped[TradeGoodModel] = relationship(back_populates="trades")
    type: Mapped[str] = mapped_column(Text(20))
    units: Mapped[Integer] = mapped_column(Integer)
    price_per_unit: Mapped[Integer] = mapped_column(Integer)
    total_price: Mapped[Integer] = mapped_column(Integer)


class MarketTradeGoodModel(Base):
    __tablename__ = "market_trade_goods"
    market_symbol: Mapped[str] = mapped_column(
        Text(20), ForeignKey(MarketModel.symbol), primary_key=True)
    good_symbol:  Mapped[str] = mapped_column(
        Text(20), ForeignKey(TradeGoodModel.symbol), primary_key=True)
    type:  Mapped[str] = mapped_column(Text(20))
    trade_volume: Mapped[Integer] = mapped_column(Integer)
    supply: Mapped[str] = mapped_column(Text(20))
    activity: Mapped[Optional[str]] = mapped_column(Text(20))
    purchase_price: Mapped[Integer] = mapped_column(Integer)
    sell_price: Mapped[Integer] = mapped_column(Integer)
