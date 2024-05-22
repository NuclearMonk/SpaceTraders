



from argparse import ArgumentParser, Namespace
import asyncio

from crud.waypoint import get_waypoint_with_symbol
from schemas.ship import Ship, ShipNavFlightMode, get_ship_list, get_ship_with_symbol
from utils.utils import console

if __name__ == "__main__":
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    ship_parser = subparsers.add_parser("ship")
    list_parser = subparsers.add_parser("list")
    ship_parser.add_argument("id", type=str)
    ship_options = ship_parser.add_mutually_exclusive_group()
    ship_options.add_argument("--negotiate", action="store_true")
    ship_options.add_argument("--deliver", type=str, nargs=3)
    
    ship_options.add_argument("-o", "--orbit", action="store_true")
    ship_options.add_argument("-d", "--dock", action="store_true")
    ship_options.add_argument("-r", "--refuel", action="store_true")
    ship_options.add_argument("-n", "--navigate", type=str)
    ship_options.add_argument("--route", type=str)
    ship_options.add_argument("-p", "--patch_navigation",
                              type=str, choices=["DRIFT", "STEALTH", "CRUISE", "BURN"])
    ship_options.add_argument("-j", "--jettison", type=str, nargs=2)
    ship_options.add_argument("--sell", type=str)
    ship_options.add_argument("--purchase", type=str, nargs=2)
    extract_options = ship_options.add_argument_group()
    extract_options.add_argument("-s", "--survey", action="store_true")
    extract_options.add_argument("-e", "--extract", action="store_true")
    args: Namespace = parser.parse_args()
    match args.command:
        case "list":
            print(*(ship.model_dump_json(indent=2)
                  for ship in get_ship_list()))
        case "ship":
            if args.id:
                ship: Ship = get_ship_with_symbol(args.id)
                ship.logger = console.print
                if args.orbit:
                    ship.orbit()
                elif args.dock:
                    ship.dock()
                elif args.navigate:
                    asyncio.run(ship.navigate(get_waypoint_with_symbol(args.navigate)))
                elif args.route:
                    asyncio.run(ship.route_navigate(get_waypoint_with_symbol(args.route)))
                elif args.patch_navigation:
                    ship.change_flight_mode(
                        ShipNavFlightMode(args.patch_navigation))
                elif args.survey:
                    ship.survey()
                elif args.extract:
                    ship.extract()
                elif args.refuel:
                    ship.refuel()
                elif args.jettison:
                    ship.jettison(args.jettison[0], int(args.jettison[1]))
                elif args.sell:
                    ship.sell(args.sell)
                elif args.purchase:
                    ship.purchase(args.purchase[0], int(args.purchase[1]))
                elif args.deliver:
                    ship.deliver_to_contract(*args.deliver)
                elif args.negotiate:
                    ship.negotiate_contract()
                else:
                    print(f"{args.id}: SHIP DATA")
                    print(ship.model_dump_json(indent=2))