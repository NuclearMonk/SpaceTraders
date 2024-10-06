from models import Base
from login import engine
from models.waypoint import *
from models.market import *
from models.contract import *
Base.metadata.create_all(engine)
