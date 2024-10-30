from models import Base
from login import engine
from models.waypoint import *
from models.market import *
from models.contract import *
from models.survey import *
from models.ship import *
from models.agent import *
from models.request import *
Base.metadata.create_all(engine)
