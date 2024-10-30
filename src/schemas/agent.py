from typing import Optional
from pydantic import BaseModel


class Agent(BaseModel):
    """
    Agent details.
    """
    accountId: Optional[str] = None
    symbol: str
    headquarters: str
    credits: int
    startingFaction: str
    shipCount: int
