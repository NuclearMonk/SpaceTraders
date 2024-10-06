from datetime import UTC
from typing import List, Optional
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from utils.utils import utcnow

from . import Base



waypoint_traits = Table(
    "waypoint_traits",
    Base.metadata,
    Column("wp_symbol", ForeignKey("waypoints.symbol"),
           primary_key=True, type_=Text(20)),
    Column("trait_symbol", ForeignKey("traits.symbol"),
           primary_key=True, type_=Text(20)),
)

waypoint_modifiers = Table(
    "waypoint_modifiers",
    Base.metadata,
    Column("wp_symbol", ForeignKey("waypoints.symbol"),
           primary_key=True, type_=Text(20)),
    Column("modifier_symbol", ForeignKey("modifiers.symbol"),
           primary_key=True, type_=Text(20)),
)


class ModifierModel(Base):
    __tablename__ = "modifiers"
    symbol: Mapped[str] = mapped_column(Text(20), primary_key=True)
    name: Mapped[str] = mapped_column(Text(30))
    description: Mapped[str] = mapped_column(Text(500))
    waypoints: Mapped[List["WaypointModel"]] = relationship(
        secondary=waypoint_modifiers, back_populates="modifiers")


class TraitModel(Base):
    __tablename__ = "traits"
    symbol: Mapped[str] = mapped_column(Text(20), primary_key=True)
    name: Mapped[str] = mapped_column(Text(30))
    description: Mapped[str] = mapped_column(Text(500))
    waypoints: Mapped[List["WaypointModel"]] = relationship(
        secondary=waypoint_traits, back_populates="traits")


class WaypointModel(Base):
    __tablename__ = "waypoints"
    symbol: Mapped[str] = mapped_column(Text(20), primary_key=True)
    system_symbol: Mapped[str] = mapped_column(Text(20))
    wp_type: Mapped[str] = mapped_column(Text(20))
    x: Mapped[int] = mapped_column(Integer)
    y: Mapped[int] = mapped_column(Integer)
    isUnderConstruction: Mapped[Optional[bool]] = mapped_column(Boolean)
    parent_symbol: Mapped[Optional[str]] = mapped_column(
        Text(20), ForeignKey("waypoints.symbol"))
    faction: Mapped[Optional[str]] = mapped_column(Text(20))
    orbits: Mapped["WaypointModel"] = relationship(back_populates="orbitals")
    orbitals: Mapped[List["WaypointModel"]] = relationship(
        back_populates="orbits", remote_side=[symbol], uselist=True, lazy='subquery')
    traits: Mapped[List[TraitModel]] = relationship(
        secondary=waypoint_traits, back_populates="waypoints")
    modifiers: Mapped[List[ModifierModel]] = relationship(
        secondary=waypoint_modifiers, back_populates="waypoints")
    time_updated = Column(DateTime(timezone=False),
                          default=utcnow, onupdate=utcnow)

    @property
    def time_updated_utc(self):
        return self.time_updated.replace(tzinfo=UTC)
