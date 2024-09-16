from argparse import ArgumentParser, Namespace
from crud.market import get_markets_in_system, get_markets_exchanging, get_markets_exporting, get_markets_importing
from crud.waypoint import get_waypoint_with_symbol


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-s", "--system", type=str)
    parser.add_argument("-i", "--imports", type=str)
    parser.add_argument("-e", "--exports", type=str)
    parser.add_argument("-x", "--exchanges", type=str)
    parser.add_argument("-d", "--distance", type=str)

    args: Namespace = parser.parse_args()
    if args.system:
        if args.imports:
            results = get_markets_importing(args.imports, args.system)
        elif args.exports:
            results = get_markets_exporting(args.exports, args.system)
        elif args.exchanges:
            results = get_markets_exchanging(args.exchanges, args.system)
        else:
            results = get_markets_in_system(args.system)
    else:
        if args.imports:
            results = get_markets_importing(args.imports)
        elif args.exports:
            results = get_markets_exporting(args.exports)
        elif args.exchanges:
            results = get_markets_exchanging(args.exchanges)

    if args.distance:
        start_point = get_waypoint_with_symbol(args.distance)
        results.sort(key=lambda x: start_point.distance_to(
            get_waypoint_with_symbol(x.symbol)))

    for result in results:
        if args.distance:
            wp = get_waypoint_with_symbol(result.symbol)
            print(f"{wp.symbol} {wp.x} {wp.y} {start_point.distance_to(wp)}")
        else:
            print(f"{result.symbol}")
        if args.system:
            for imp in result.imports:
                print(f"<- {imp.name}")
            for exp in result.exports:
                print(f"-> {exp.name}")
            for exch in result.exchange:
                print(f"<> {exch.name}")
