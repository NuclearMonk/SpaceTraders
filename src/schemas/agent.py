from typing import Optional
from pydantic import BaseModel

from schemas.faction import FactionSymbol


class Agent(BaseModel):
    """
    Agent details.
    """
    accountId: Optional[str] = None
    symbol: str
    headquarters: str
    credits: int
    startingFaction: FactionSymbol
    shipCount: int
