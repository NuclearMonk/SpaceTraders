

from typing import List


from crud.job import assign_job, get_ships_with_job
from management.hauler import Hauler
from management.job import JobAssignment
from management.transport_order import TransportOrder
from schemas.ship import Ship
from st_requests.ship import get_ship





class TransportManager:

    def __init__(self) -> None:
        self.haulers: List[Hauler] = [Hauler(get_ship(
            symbol))for symbol in get_ships_with_job(JobAssignment.HAULER)]
        self.unassigned_transport_orders: List[TransportOrder] = []

    def add_hauler(self, ship: Ship) -> bool:
        assign_job(ship, JobAssignment.HAULER)
        self.haulers.append(Hauler(ship))

        return True

    def add_transport_order(self, order: TransportOrder):
        print(f"got new transport order:")
        self.unassigned_transport_orders.append(order)


    def assign_order(self):
        # for now we assigned one order per ship so all units get assigned right away
        if not self.unassigned_transport_orders:
            return
        for hauler in self.haulers:
            if not hauler.transport_order:
                order = self.unassigned_transport_orders.pop()
                print(f"assigning order to {hauler.ship.symbol}: {order}")
                hauler.assign_transport_order(order)
                order.units_assigned = order.units_total
                return

    def do_cycle(self) -> bool:
        self.assign_order()
        for hauler in self.haulers:
            if hauler.do_tick():
                return True
            
        return False
