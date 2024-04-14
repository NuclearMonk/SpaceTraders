import argparse
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from requests import get

from utils import print_json
from waypoint import WaypointSymbol
from login import HEADERS


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


def get_market(symbol: WaypointSymbol) -> Optional[Market]:
    response = get(f"https://api.spacetraders.io/v2/systems/{
                   symbol.system_string}/waypoints/{symbol.waypoint_string}/market", headers=HEADERS)
    if response.ok:
        js = response.json()
        print(js)
        return Market.model_validate(js["data"])
    else:
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("symbol")
    parser.add_argument("-s", "--search")
    args = parser.parse_args()
    if args.symbol:
        if market := get_market(WaypointSymbol(*WaypointSymbol.split_symbol(args.symbol))):
            print(market)
    else:
        print("ERROR GETTING SYSTEM DATA")
