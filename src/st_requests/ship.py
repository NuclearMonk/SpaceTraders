

from typing import List
from login import get,post
from schemas.ship import Ship



def get_ships()-> List[Ship]:
    '''gets all the ships from the server then\nupdates them in the local database, then returns them'''
    ...