from sqlalchemy import Boolean, Column, DateTime, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from models import Base


class ContractModel(Base):
    __tablename__ = "contracts"
    id: Mapped[str] = mapped_column(Text(20), primary_key=True)
    faction_symbol: Mapped[str] = mapped_column(Text(20))
    contract_type: Mapped[str] = mapped_column(Text(20))
    terms_deadline = Column(DateTime(timezone=False))
    terms_pay_accepted: Mapped[int] = mapped_column(Integer)
    terms_pay_fulfilled: Mapped[int] = mapped_column(Integer)
    deliver_trade_symbol: Mapped[str] = mapped_column(
        Text(20), primary_key=True)
    deliver_symbol = mapped_column(Text(20), primary_key=True)
    deliver_units_required: Mapped[int] = mapped_column(Integer)
    deliver_units_fulfilled: Mapped[int] = mapped_column(Integer)
    accepted: Mapped[Boolean] = mapped_column(Boolean)
    fulfilled: Mapped[Boolean] = mapped_column(Boolean)
    deadline_to_accept = Column(DateTime(timezone=False))
