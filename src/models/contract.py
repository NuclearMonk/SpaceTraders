from typing import List
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models import Base
from models.market import TradeGoodModel
from models.waypoint import WaypointModel


class ContractDeliveryModel(Base):
    __tablename__ = "contract_deliveries"
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    contract_id: Mapped[str] = mapped_column(
        Text(20), ForeignKey("contracts.id"))
    contract: Mapped["ContractModel"] = relationship(back_populates="deliver")
    delivery_symbol: Mapped[str] = mapped_column(
        Text(20), ForeignKey("waypoints.symbol"))
    trade_symbol: Mapped[str] =mapped_column(
        Text(20), ForeignKey("trade_goods.symbol"))
    required: Mapped[int] = mapped_column(Integer)
    fulfilled: Mapped[int] = mapped_column(Integer)


class ContractModel(Base):
    __tablename__ = "contracts"
    id: Mapped[str] = mapped_column(Text(20), primary_key=True)
    faction_symbol: Mapped[str] = mapped_column(Text(20))
    contract_type: Mapped[str] = mapped_column(Text(20))
    terms_deadline = Column(DateTime(timezone=False))
    terms_pay_accepted: Mapped[int] = mapped_column(Integer)
    terms_pay_fulfilled: Mapped[int] = mapped_column(Integer)
    deliver: Mapped[List[ContractDeliveryModel]
                    ] = relationship(back_populates="contract")
    accepted: Mapped[Boolean] = mapped_column(Boolean)
    fulfilled: Mapped[Boolean] = mapped_column(Boolean)
    deadline_to_accept = Column(DateTime(timezone=False))
