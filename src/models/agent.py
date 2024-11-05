from typing import Any
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models import Base
from models.waypoint import WaypointModel
from schemas.faction import FactionSymbol
from utils.utils import utcnow


class AgentModel(Base):
    __tablename__ = "agents"
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(Text(20))
    headquarters_symbol = Column(Text(20), ForeignKey(WaypointModel.symbol))
    headquarters: Mapped[WaypointModel] = relationship()
    credits: Mapped[int] = mapped_column(Integer)
    starting_faction: Mapped[FactionSymbol] = mapped_column(Enum(FactionSymbol))
    ship_count: Mapped[int] = mapped_column(Integer)
    timestamp: Mapped[DateTime] = Column(DateTime(timezone=False),
                                         default=utcnow)

    def __init__(self,
                 symbol:str,
                 headquarters: WaypointModel,
                 credits: int,
                 starting_faction: FactionSymbol, ship_count: int, **kw: Any):
        super().__init__(**kw)
        self.symbol = symbol
        self.headquarters = headquarters
        self.credits = credits
        self.starting_faction = starting_faction
        self.ship_count = ship_count
