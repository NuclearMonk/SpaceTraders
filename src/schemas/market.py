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






# if __name__ == "__main__":
#     parser = argparse.ArgumentParser()
#     parser.add_argument("symbol")
#     parser.add_argument("-s", "--search")
#     args = parser.parse_args()
#     if args.symbol:
#         if not is_system_symbol(args.symbol):
#             if market := get_market(get_waypoint_with_symbol(args.symbol)):
#                 print(market.model_dump_json(indent=2))
#         else:
#             print_json(get_all_markets(get_system_with_symbol(args.symbol)))
