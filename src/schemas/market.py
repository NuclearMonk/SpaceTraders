from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field




class Good(BaseModel):
    symbol: str
    name: str
    description: str


class MarketTransaction(BaseModel):
    waypointSymbol: str
    shipSymbol: str
    tradeSymbol: str
    type_field: str = Field(alias="type")
    units: int
    pricePerUnit: int
    totalPrice: int
    timestamp: datetime


class MarketTradeGood(BaseModel):
    symbol: str
    type: str
    tradeVolume: int
    supply: str
    activity: Optional[str] = None
    purchasePrice: int
    sellPrice: int


class Market(BaseModel):
    symbol: str
    exports: List[Good]
    imports: List[Good]
    exchange: List[Good]
    transactions: Optional[List[MarketTransaction]] = None
    tradeGoods: Optional[List[MarketTradeGood]] = None
