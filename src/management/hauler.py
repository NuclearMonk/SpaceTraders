

from management.navigable import Navigable
from management.transport_order import TransportOrder
from schemas.ship import Ship
from state_machine.state_machine import StateMachine, Transition
from state_machine.states.sm_deliver import SMDeliver
from state_machine.states.sm_pickup import SMPickup
from state_machine.states.waiting import StateWaiting


class Hauler(Navigable):

    def __init__(self, ship: Ship) -> None:
        super().__init__(ship)
        self.transport_order: TransportOrder = None
        self.state_machine = StateMachine('Hauler SM',
                                          [StateWaiting('Awaiting Order', self.ship),
                                           SMPickup(
                                               'Pickup SM', self, lambda: self.transport_order),
                                           SMDeliver('Delivery SM', self, lambda: self.transport_order)],
                                          [
                                              Transition(
                                                  'Awaiting Order', 'Delivery SM', lambda: self.__ready_to_deliver, "All Picked Up or Cargo Full"),
                                              Transition(
                                                  'Awaiting Order', 'Pickup SM', lambda: self.transport_order != None, "Has Transport Order"),
                                              Transition(
                                                  'Pickup SM', 'Delivery SM', lambda: self.__ready_to_deliver, "All Picked Up or Cargo Full"),
                                              Transition(
                                                  'Delivery SM', 'Awaiting Order', lambda: self.__all_delivered, "All Done"),
                                              Transition(
                                                  'Delivery SM', 'Awaiting Order', lambda: not self.transport_order, "All Done"),
                                              Transition(
                                                  'Delivery SM', 'Pickup SM', lambda: self.__has_to_pickup_more, "Not Done")
                                          ], 'Awaiting Order', root=True
                                          )

    def do_tick(self):
        x = self.state_machine.do_tick()
        if self.transport_order and self.transport_order.units_delivered == self.transport_order.units_total:
            self.transport_order = None
        return x

    def assign_transport_order(self, transport_order: TransportOrder):
        self.transport_order = transport_order

    @property
    def __ready_to_deliver(self) -> bool:
        if not self.transport_order:
            return False
        if self.transport_order.units_total == self.transport_order.units_picked_up:
            return True
        if self.ship.cargo.capacity_remaining == 0:
            return True
        return False

    @property
    def __all_delivered(self) -> bool:
        if not self.transport_order:
            return False
        return self.transport_order.units_total == self.transport_order.units_delivered

    @property
    def __has_to_pickup_more(self) -> bool:
        if not self.transport_order:
            return False
        if self.ship.cargo.capacity_remaining== 0:
            return False
        return self.transport_order.units_total > (self.transport_order.units_delivered + self.transport_order.units_picked_up)
