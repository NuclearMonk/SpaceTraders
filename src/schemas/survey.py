from collections import Counter
from datetime import datetime, timedelta
from typing import List
from pydantic import BaseModel, field_serializer

from utils.utils import format_time_ms, time_until


class SurveyDeposit(BaseModel):
    symbol: str

class Survey(BaseModel):
    signature: str
    symbol: str
    deposits : List[SurveyDeposit]
    expiration: datetime
    size : str

    @field_serializer('expiration')
    def custom_time_dump(self, expiration : datetime, _info):
        return f"{datetime.strftime(expiration, "%Y-%m-%dT%H:%M:%S.%f")[:-3]}Z"

    @property
    def is_valid(self)->bool:
        return time_until(self.expiration) > timedelta(0)

    def count(self, symbol: str)-> int:
        return [deposit.symbol for deposit in self.deposits].count(symbol)

    def matching_deposit_count(self, look_for : List[str])-> int:
        c = Counter(deposit.symbol for deposit in self.deposits)
        return sum(c[symbol] for symbol in look_for)

    def rank_survey(self, look_for : List[str])-> float:
        return self.matching_deposit_count(look_for)/ len(self.deposits)