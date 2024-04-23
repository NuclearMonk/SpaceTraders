import argparse
from crud.waypoint import get_waypoint_with_symbol, get_waypoints_in_system
from schemas.navigation import get_system_with_symbol

if __name__ == "__main__":
    #print(get_waypoint_with_symbol("X1-VD53-B21"))
    parser = argparse.ArgumentParser()
    parser.add_argument("symbol")
    args = parser.parse_args()
    if args.symbol:
        system = get_system_with_symbol(args.symbol)
        #for waypoint in system.waypoints:
            #get_waypoint_with_symbol(waypoint.symbol)

    print(*(wp.symbol for wp  in get_waypoints_in_system(args.symbol, "MARKETPLACE")), sep="\n")