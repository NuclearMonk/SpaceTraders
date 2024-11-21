

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, override


from crud.job import assign_job, get_ships_with_job
from management.job import JobAssignment
from pathfinding.pathfinding import calculate_route
from schemas.contract import Contract
from schemas.market import TradeGood
from schemas.navigation import Waypoint
from schemas.ship import Ship, ShipNavStatus
from st_requests.market import get_market
from st_requests.ship import get_ship
from st_requests.waypoint import get_waypoint


@dataclass
class TransportOrder:
    good: TradeGood
    units_total: int
    pickup_wp: Waypoint
    delivery_wp: Waypoint
    units_picked_up: int = 0
    units_delivered: int = 0
    units_assigned: int = 0
    pickup_ship: Optional[Ship] = None
    delivery_ship: Optional[Ship] = None
    contract: Optional[Contract] = None

    def __str__(self) -> str:
        return f"{self.pickup_wp.symbol}({self.pickup_ship.symbol if self.pickup_ship else ""})->{self.delivery_wp.symbol}({self.delivery_ship.symbol if self.delivery_ship else ""}) {self.good.symbol} {self.units_delivered}/{self.units_total}"


class TransportManager:

    def __init__(self) -> None:
        self.haulers: List[Ship] = [get_ship(
            symbol)for symbol in get_ships_with_job(JobAssignment.HAULER)]
        self.transport_orders: List[TransportOrder] = []
        self.order_assignment: Dict[str, TransportOrder] = {
            hauler.symbol: None for hauler in self.haulers}
        self.transport_routes: Dict[str, Optional[List[Tuple[Waypoint, bool]]]] = {
            hauler.symbol: None for hauler in self.haulers}

    def add_hauler(self, ship: Ship) -> bool:
        if ship in self.haulers:
            return False
        assign_job(ship, JobAssignment.HAULER)
        self.haulers.append(ship)
        self.order_assignment[ship.symbol] = None
        self.transport_routes[ship.symbol] = None
        return True

    def add_transport_order(self, order: TransportOrder):
        print(f"got new transport order:")
        self.transport_orders.append(order)

    def get_assignable_order(self) -> Optional[TransportOrder]:
        for order in self.transport_orders:
            if order.units_total > order.units_assigned:
                return order
        return None

    def assign_order(self, hauler: Ship, order: TransportOrder):
        # for now we assigned one order per ship so all units get assigned right away
        print(f"assigning order to {hauler.symbol}: {order}")
        self.order_assignment[hauler.symbol] = order
        order.units_assigned = order.units_total

    def do_cycle(self) -> bool:
        for hauler in self.haulers:
            if hauler.nav.live_status == ShipNavStatus.IN_TRANSIT:
                continue
            if not self.order_assignment.get(hauler.symbol, None):
                # if we dont have an order assigned then we
                # check if theres any assignable orders
                if order := self.get_assignable_order():
                    # if there are any, assign it and go from there
                    self.assign_order(hauler, order)
                else:
                    # we just skip this ship
                    continue
            order = self.order_assignment.get(hauler.symbol)
            route = self.transport_routes.get(hauler.symbol)

            if route:
                if self.follow_route(hauler, route):
                    return True

                    # we should be delivering so

            if (hauler.nav.waypointSymbol == order.delivery_wp.symbol and
                    hauler.cargo.get_item_count(order.good.symbol) > 0):
                # if we are at the delivery location
                # and have any deliverable goods
                self.deliver(hauler, order)
                return True

            if (hauler.nav.waypointSymbol == order.pickup_wp.symbol and
                    hauler.cargo.capacity_remaining > 0 and
                    order.units_picked_up < order.units_total):
                # if we are at the correct pickup location
                # and we still have space for cargo
                # and we still need to pickup cargo
                self.pickup(hauler, order)
                return True

            if hauler.cargo.capacity_remaining > 0 and (order.units_delivered == order.units_picked_up):
                self.set_route_to_pickup(hauler, order)
                if self.follow_route(hauler, route):
                    return True
                continue
            self.set_route_to_delivery(hauler, order)
            if self.follow_route(hauler, route):
                return True
        return False

    def follow_route(self, hauler: Ship, route: List[Tuple[Waypoint, bool]]) -> bool:
        if not route:
            return False
        wp, refuel = route[0]
        if hauler.nav.live_status == ShipNavStatus.IN_TRANSIT:
            return False
        if hauler.nav.waypointSymbol == wp.symbol:
            if not refuel:
                if hauler.nav.live_status == ShipNavStatus.DOCKED:
                    hauler.orbit()
                    return True
                route.pop(0)
                if not route:
                    return False
                hauler.navigate(route[0][0])
                return True
            if hauler.fuel.current < hauler.fuel.capacity:
                if hauler.nav.live_status == ShipNavStatus.IN_ORBIT:
                    hauler.dock()
                    return True
                hauler.refuel()
                return True
        route.pop(0)
        if not route:
            return False
        if hauler.nav.live_status == ShipNavStatus.DOCKED:
            hauler.orbit()
            return True
        hauler.navigate(route[0][0])
        return True

    def set_route_to_pickup(self, hauler: Ship, order: TransportOrder) -> bool:
        # check if we have a route
        self.transport_routes[hauler.symbol] = calculate_route(hauler.nav.waypointSymbol,
                                                               order.pickup_wp.symbol,
                                                               hauler.fuel.capacity,
                                                               hauler.fuel.current)

    def pickup(self, hauler: Ship, order: TransportOrder) -> bool:
        if order.pickup_ship:
            if hauler.nav.live_status == order.pickup_ship.nav.live_status:
                # if they are the same we can transfer the cargo:
                # the amount to pickup is
                # the remaining cargo space in the hauler
                # or the amount left to pick up on the order
                pickup_units = min(hauler.cargo.capacity_remaining,
                                   order.units_total-order.units_picked_up)
                # update the contract
                if order.pickup_ship.transfer_cargo(
                        hauler, order.good, pickup_units):
                    order.units_picked_up += pickup_units

                # we did make a server request and are done here anyways
                return True
            if order.pickup_ship.nav.live_status == ShipNavStatus.DOCKED:
                # if the ship is docked then we must dock
                hauler.dock()
                return True
            else:
                hauler.orbit()
                return True
        # we are instead buying from a market
        if hauler.nav.live_status == ShipNavStatus.IN_ORBIT:
            # we must dock to buy at a marker
            hauler.dock()
            return True
        # the amount to pickup is
        # the remaining cargo space in the hauler
        # or the amount left to pick up on the order
        # or 20, the trade volume for the market
        market = get_market(hauler.nav.waypointSymbol, True)
        purchase_ = min(hauler.cargo.capacity_remaining,
                        order.units_total-order.units_picked_up,
                        market.trade_good_trade_volume(order.good))
        if hauler.purchase(order.good, purchase_):
            order.units_picked_up += purchase_
        return True

    def set_route_to_delivery(self, hauler: Ship, order: TransportOrder):
        self.transport_routes[hauler.symbol] = calculate_route(hauler.nav.waypointSymbol,
                                                               order.delivery_wp.symbol,
                                                               hauler.fuel.capacity,
                                                               hauler.fuel.current)

    def deliver(self, hauler: Ship, order: TransportOrder) -> bool:
        if order.delivery_ship:
            if hauler.nav.live_status == order.delivery_ship.nav.live_status:
                # if they are the same we can transfer the cargo:
                # the amount to pickup is
                # the remaining cargo space in the hauler
                # or the amount left to pick up on the order
                deliver_units = min(hauler.cargo.get_item_count(order.good.symbol),
                                    order.units_total-order.units_delivered)
                # update the contract
                if hauler.transfer_cargo(
                        order.delivery_ship, order.good, deliver_units):
                    order.units_delivered = deliver_units
                # we did make a server request and are done here anyways
                return True
            if order.pickup_ship.nav.live_status == ShipNavStatus.DOCKED:
                # if the ship is docked then we must dock
                hauler.dock()
                return True
            else:
                hauler.orbit()
                return True
        if order.contract:
            if hauler.nav.live_status != ShipNavStatus.DOCKED:
                # we must be docked to deliver to contract
                hauler.dock()
                return True
            deliver_units = min(hauler.cargo.get_item_count(order.good.symbol),
                                order.units_total-order.units_delivered)
            if hauler.deliver_to_contract(
                    order.contract, order.good, deliver_units):
                order.units_delivered += deliver_units
            return True
        print(hauler.nav.live_status)
        if hauler.nav.live_status == ShipNavStatus.IN_ORBIT:
            # we must dock sell at a marker
            hauler.dock()
            return True
        # the amount to del
        # iver is
        # the remaining cargo space in the hauler
        # or the amount left to pick up on the order
        market = get_market(hauler.nav.waypointSymbol, True)
        sell_units = min(hauler.cargo.get_item_count(order.good.symbol),
                         order.units_total-order.units_delivered,
                         market.trade_good_trade_volume(order.good))
        if hauler.sell(order.good, sell_units):
            order.units_delivered += sell_units
        return True
