from datetime import datetime
from typing import List
from pydantic import BaseModel


class SurveyDeposit(BaseModel):
    symbol: str

class Survey(BaseModel):
    signature: str
    symbol: str
    deposits : List[SurveyDeposit]
    expiration: datetime
    size : str
