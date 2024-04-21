from typing import List, Optional
from sqlalchemy import Boolean, ForeignKey, Integer, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
# symbol x
# type x
# systemSymbol x
# x x
# y x
# orbitals x
# orbit x
# faction #
# traits
# modifiers
# chart
# isUnderConstruction


class Base(DeclarativeBase):
    ...

class WaypointTrait(Base):
    __tablename__ = "waypoint_traits"
    symbol: Mapped[str] = mapped_column(Text(20), primary_key=True)
    name: Mapped[str] = mapped_column(Text(30))
    description: Mapped[str] = mapped_column(Text(500))


class WaypointModel(Base):
    __tablename__ = "waypoints"
    symbol: Mapped[str] = mapped_column(Text(20), primary_key=True)
    systemSymbol: Mapped[str] = mapped_column(Text(20))
    wp_type: Mapped[str] = mapped_column(Text(20))
    x: Mapped[int] = mapped_column(Integer)
    y: Mapped[int] = mapped_column(Integer)
    isUnderConstruction: Mapped[Optional[bool]] = mapped_column(Boolean)
    parent_symbol: Mapped[Optional[str]] = mapped_column(
        Text(20), ForeignKey("waypoints.symbol"))
    faction : Optional[Mapped[str]] = mapped_column(Text(20))
    orbits: Mapped["WaypointModel"] = relationship(back_populates="orbitals")
    orbitals: Mapped[List["WaypointModel"]] = relationship(
        back_populates="orbits", remote_side=[symbol], uselist=True)
