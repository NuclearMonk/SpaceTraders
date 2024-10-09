import argparse
import pprint
from typing import Optional

from pydantic import ValidationError
from crud import get_waypoint_with_symbol, get_market_with_symbol, get_all_contracts, refresh_contract_cache, get_open_contracts
from schemas.navigation import System, is_system_symbol
from utils.utils import system_symbol_from_wp_symbol
from login import SYSTEM_BASE_URL, get

if __name__ == "__main__":
    refresh_contract_cache()
    print(get_all_contracts())
    print(get_open_contracts())
    # parser = argparse.ArgumentParser()
    # parser.add_argument("symbol")
    # args = parser.parse_args()
    # if args.symbol:
    #     system = get_system_with_symbol(args.symbol)
    #     for waypoint in system.waypoints:
    #         wp = get_waypoint_with_symbol(waypoint.symbol)
    #         if wp.has_trait("MARKETPLACE"):
    #             get_market_with_symbol(wp.symbol)


def get_system_with_symbol(symbol: str) -> Optional[System]:
    if is_system_symbol(symbol):
        system_symbol = symbol
    else:
        system_symbol = system_symbol_from_wp_symbol(symbol)
    response = get(f"{SYSTEM_BASE_URL}/{system_symbol}")
    if response.ok:
        js = response.json()
        try:
            return System.model_validate(js["data"])
        except ValidationError as e:
            print(e)
            return None
    print(response)
    return None