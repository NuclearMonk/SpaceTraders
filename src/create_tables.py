from sqlalchemy import create_engine
from models.waypoint import Base
from login import engine
Base.metadata.create_all(engine)