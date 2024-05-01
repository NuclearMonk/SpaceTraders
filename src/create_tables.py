from sqlalchemy import create_engine
from models import Base
from login import engine
from models.waypoint import *
from models.market import *
Base.metadata.create_all(engine)