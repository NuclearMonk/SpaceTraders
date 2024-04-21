import argparse
from crud.waypoint import get_waypoint
from schemas.navigation import get_system_with_symbol

if __name__ == "__main__":
    print(get_waypoint("X1-VD53-B21"))
    parser = argparse.ArgumentParser()
    parser.add_argument("symbol")
    args = parser.parse_args()
    if args.symbol:
        system = get_system_with_symbol(args.symbol)
        for waypoint in system.waypoints:
            print(get_waypoint(waypoint.symbol))
