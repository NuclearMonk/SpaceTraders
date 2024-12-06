

from typing import Callable, Tuple
from management.navigable import Navigable
from management.transport_order import TransportOrder
from schemas.market import TradeGood
from schemas.ship import ShipNavStatus
from state_machine.state_machine import StateMachine, Transition
from state_machine.states.pickup_from_ship import StatePickupFromShip
from state_machine.states.purchase import StatePurchase
from state_machine.states.sm_travel import SMTravel


class SMPickup(StateMachine):

    def __init__(self, name, navigable: Navigable, get_order: Callable[[], TransportOrder], root=False) -> None:
        self.navigable = navigable
        self.get_order = get_order
        self.order = None
        super().__init__(name,
                         [
                             SMTravel('Traveling', self.navigable),
                             StatePurchase('Purchase From Market', self.navigable.ship,
                                           self.__get_pickup_data, lambda x: self.order_pickup(x)),
                             StatePickupFromShip('Pickup From Ship', self.navigable.ship, lambda: self.order.pickup_ship,
                                                 self.__get_pickup_data, lambda x: self.order_pickup(x))

                         ],
                         [
                             Transition('Traveling', 'Pickup From Ship',
                                        lambda: self.__at_pickup_location and self.order.pickup_ship, "Pickup Ship"),
                             Transition('Traveling', 'Purchase From Market',
                                        lambda: self.__at_pickup_location and not self.order.pickup_ship, "No Pickup Ship"),
                         ], 'Traveling'
                         )


    def on_enter(self):
        self.navigable.ship.log(f"ENTERING:{self.name}")
        return super().on_enter()

    def on_exit(self):
        self.navigable.ship.log(f"EXITING:{self.name}")
        return super().on_exit()
    
    @property
    def __at_pickup_location(self):
        wp, status = self.__get_pickup_location()
        return (self.navigable.ship.nav.route.destination.symbol == wp.symbol
                and self.navigable.ship.nav.live_status == status)

    def __get_pickup_data(self) -> Tuple[TradeGood, int]:
        return self.order.good, min(self.order.units_total-self.order.units_picked_up,
                                    self.navigable.ship.cargo.capacity_remaining)

    def __get_pickup_location(self):
        if not self.order:
            return None
        if self.order.pickup_ship:
            return self.order.pickup_wp, self.order.pickup_ship.nav.live_status
        return self.order.pickup_wp, ShipNavStatus.DOCKED

    def order_pickup(self, units: int):
        self.order.units_picked_up += units

    def on_enter(self):
        self.order = self.get_order()
        if x := self.__get_pickup_location():
            self.navigable.set_destination(x[0], x[1])
        return super().on_enter()
