import argparse
from crud import get_waypoint_with_symbol, get_market_with_symbol
from schemas.navigation import get_system_with_symbol

if __name__ == "__main__":
    # print(get_waypoint_with_symbol("X1-VD53-B21"))
    parser = argparse.ArgumentParser()
    parser.add_argument("symbol")
    args = parser.parse_args()
    if args.symbol:
        system = get_system_with_symbol(args.symbol)
        for waypoint in system.waypoints:
            wp = get_waypoint_with_symbol(waypoint.symbol)
            if wp.has_trait("MARKETPLACE"):
                get_market_with_symbol(wp.symbol)
