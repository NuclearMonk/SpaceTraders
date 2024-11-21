from typing import Any
from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from management.job import JobAssignment
from models.ship import ShipModel
from models.waypoint import WaypointModel
from schemas.navigation import Waypoint
from schemas.ship import Ship
from . import Base


class JobAssignmentsModel(Base):
    __tablename__ = 'job_assignments'
    symbol: Mapped[str] = mapped_column(
        ForeignKey(ShipModel.symbol), primary_key=True)
    job: Mapped[JobAssignment] = mapped_column(Enum(JobAssignment))

    def __init__(self, ship: Ship, job: JobAssignment, **kw: Any):
        super().__init__(**kw)
        self.symbol = ship.symbol
        self.job = job


class MinerAssignmentsModel(Base):
    __tablename__ = 'miner_assignments'
    symbol: Mapped[str] = mapped_column(
        ForeignKey(ShipModel.symbol), primary_key=True)
    waypoint_symbol: Mapped[str] = mapped_column(
        ForeignKey(WaypointModel.symbol))

    def __init__(self, ship: Ship, waypoint: Waypoint, **kw: Any):
        super().__init__(**kw)
        self.symbol = ship.symbol
        self.waypoint_symbol = waypoint.symbol
