from typing import Any, List
from sqlalchemy import Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models import Base
from schemas.faction import FactionSymbol
from schemas.navigation import SystemType, WaypointFaction


class SystemFactionModel(Base):
    __tablename__ = 'system_factions'
    system_symbol: Mapped[str] = mapped_column(
        ForeignKey("systems.symbol"), primary_key=True)
    faction_symbol: Mapped[FactionSymbol] = mapped_column(
        Enum(FactionSymbol), primary_key=True)

    def __init__(self,
                 system_symbol:str,
                 faction_symbol: FactionSymbol,
                   **kw: Any):
        super().__init__(**kw)
        self.system_symbol= system_symbol
        self.faction_symbol= faction_symbol


class SystemModel(Base):
    __tablename__ = 'systems'
    symbol: Mapped[str] = mapped_column(Text(20), primary_key=True)
    sector_symbol: Mapped[str] = mapped_column(Text(20))
    type: Mapped[SystemType] = mapped_column(Enum(SystemType))
    x: Mapped[int] = mapped_column()
    y: Mapped[int] = mapped_column()
    waypoints: Mapped[List['WaypointModel']
                      ] = relationship(back_populates='system')
    factions: Mapped[List[SystemFactionModel]] = relationship(
        uselist=True, cascade='save-update, merge, delete, delete-orphan')

    def __init__(self,
                 symbol: str,
                 sector_symbol: str,
                 type: SystemType,
                 x: int,
                 y: int,
                 waypoints: List['WaypointModel'],
                 faction: List[SystemFactionModel], **kw: Any):
        super().__init__(**kw)
        self.symbol = symbol
        self.sector_symbol = sector_symbol
        self.type = type
        self.x = x
        self.y = y
        self.waypoints = waypoints
        self.faction = faction
