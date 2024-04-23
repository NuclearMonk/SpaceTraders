import argparse
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from utils.utils import print_json
from schemas.navigation import Waypoint, System, get_system_with_symbol, is_system_symbol, system_symbol_from_wp_symbol
from crud.waypoint import get_waypoint_with_symbol
from login import HEADERS, SYSTEM_BASE_URL, get
from crud.waypoint import get_waypoints_in_system


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


def get_market(wp: Waypoint) -> Optional[Market]:
    response = get(f"{SYSTEM_BASE_URL}/{system_symbol_from_wp_symbol(wp.symbol)}/waypoints/{wp.symbol}/market", headers=HEADERS)
    if response.ok:
        js = response.json()
        print(js)
        return Market.model_validate(js["data"])
    else:
        return None

def get_all_markets(system: System)-> List[Market]:
    market_waypoints = get_waypoints_in_system(system.symbol, "MARKETPLACE")
    markets = [get_market(waypoint) for waypoint in market_waypoints]
    return markets



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("symbol")
    parser.add_argument("-s", "--search")
    args = parser.parse_args()
    if args.symbol:
        if not is_system_symbol(args.symbol):
            if market := get_market(get_waypoint_with_symbol(args.symbol)):
                print(market.model_dump_json(indent=2))
        else:
            print_json(get_all_markets(get_system_with_symbol(args.symbol)))
