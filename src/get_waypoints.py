import argparse
from crud import get_waypoint_with_symbol, get_waypoints_in_system
from crud.market import get_market_with_symbol
from schemas.navigation import Waypoint

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("symbol")
    parser.add_argument("-s", "--search")
    parser.add_argument("-m", "--market", action="store_true")
    args = parser.parse_args()
    if args.symbol:
        start_point: Waypoint = get_waypoint_with_symbol(args.symbol)
        print(start_point.model_dump_json(indent=2))
        if args.market:
            print(get_market_with_symbol(
                start_point.symbol).model_dump_json(indent=2))
    if args.search == "MARKETPLACE":
        if wps := get_waypoints_in_system(start_point.systemSymbol, "MARKETPLACE"):
            wps.sort(key=start_point.distance_to)
            for wp in wps:
                print(wp.symbol, wp.x, wp.y, start_point.distance_to(wp))
                market = get_market_with_symbol(wp.symbol)
                for imp in market.imports:
                    print(f"<- {imp.name}")
                for exp in market.exports:
                    print(f"-> {exp.name}")
                for exch in market.exchange:
                    print(f"<> {exch.name}")
        else:
            "ERROR GETTING SYSTEM DATA"
    elif args.search:
        if wps := get_waypoints_in_system(start_point.systemSymbol):
            wps.sort(key=start_point.distance_to)
            for wp in wps:
                print(wp.symbol, wp.x, wp.y, start_point.distance_to(wp))
        else:
            "ERROR GETTING SYSTEM DATA"
    else:
        "ERROR GETTING SYSTEM DATA"
