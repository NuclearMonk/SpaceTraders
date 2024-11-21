from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from crud.waypoint import _get_waypoint
from management.job import JobAssignment
from models.job_assignments import JobAssignmentsModel, MinerAssignmentsModel
from schemas.navigation import Waypoint
from schemas.ship import Ship
from login import engine


def assign_job(ship: Ship, job: JobAssignment):
    with Session(engine) as session:
        if model := session.scalar(select(JobAssignmentsModel).where(JobAssignmentsModel.symbol == ship.symbol)):
            model.job = job
            session.commit()
            return
        session.add(JobAssignmentsModel(ship, job))
        session.commit()


def get_job(ship: Ship) -> Optional[JobAssignment]:
    with Session(engine) as session:
        if model := session.scalar(select(JobAssignmentsModel).where(JobAssignmentsModel.symbol == ship.symbol)):
            return model.job
        return None


def assign_miner_waypoint(ship: Ship, waypoint: Waypoint):
    with Session(engine) as session:
        if model := session.scalar(select(MinerAssignmentsModel).where(MinerAssignmentsModel.symbol == ship.symbol)):
            model.waypoint_symbol = waypoint.symbol
            session.commit()
        session.add(MinerAssignmentsModel(ship, waypoint))
        session.commit()


def get_ships_with_job(job: JobAssignment) -> List[str]:
    with Session(engine) as session:
        return session.scalars(select(JobAssignmentsModel.symbol).where(JobAssignmentsModel.job == job))


def get_miners_at_waypoint(waypoint: Waypoint) -> Optional[List[str]]:
    with Session(engine) as session:
        if models := session.scalars(select(MinerAssignmentsModel).where(MinerAssignmentsModel.waypoint_symbol == waypoint.symbol)):
            return [model.symbol for model in models]
        return None


def get_miner_waypoint(ship: Ship) -> Optional[str]:
    with Session(engine) as session:
        if model := session.scalar(select(MinerAssignmentsModel).where(MinerAssignmentsModel.symbol == ship.symbol)):
            return model.waypoint_symbol
        return None
