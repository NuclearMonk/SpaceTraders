

from typing import Callable, Tuple
from management.navigable import Navigable
from management.transport_order import TransportOrder
from schemas.market import TradeGood
from schemas.ship import ShipNavStatus
from state_machine.state_machine import StateMachine, Transition
from state_machine.states.deliver_to_contract import StateDeliverToContract
from state_machine.states.deliver_to_ship import StateDeliverToShip
from state_machine.states.pickup_from_ship import StatePickupFromShip
from state_machine.states.purchase import StatePurchase
from state_machine.states.sell import StateSell
from state_machine.states.sm_travel import SMTravel


class SMDeliver(StateMachine):

    def __init__(self, name, navigable: Navigable, get_order: Callable[[], TransportOrder], root=False) -> None:
        self.navigable = navigable
        self.get_order = get_order
        self.order = None
        super().__init__(name,
                         [
                             SMTravel('Traveling', self.navigable),
                             StateSell('Sell At Market', self.navigable.ship,
                                           self.__get_delivery_data, lambda x: self.order_deliver(x)),
                             StateDeliverToShip('Deliver To Ship', self.navigable.ship, lambda: self.order.pickup_ship,
                                                self.__get_delivery_data, lambda x: self.order_deliver(x)),
                             StateDeliverToContract('Deliver To Contract', self.navigable.ship,
                                                    lambda: self.order.contract, self.__get_delivery_dat, lambda x: self.order_deliver(x))

                         ],
                         [
                             Transition('Traveling', 'Deliver To Contract',
                                        lambda: self.__at_delivery_location and self.order.contract, "Order Contract"),
                             Transition('Traveling', 'Deliver To Ship',
                                        lambda: self.__at_delivery_location and self.order.delivery_ship, "Order Ship"),
                             Transition('Traveling', 'Sell At Market',
                                        lambda: self.__at_delivery_location, "Order Market"),
                         ], 'Traveling'
                         )


    def on_enter(self):
        self.navigable.ship.log(f"ENTERING:{self.name}")
        return super().on_enter()

    def on_exit(self):
        self.navigable.ship.log(f"EXITING:{self.name}")
        return super().on_exit()
    
    @property
    def __at_delivery_location(self):
        wp, status = self.__get_delivery_location()
        return (self.navigable.ship.nav.route.destination.symbol == wp.symbol 
                and self.navigable.ship.nav.live_status == status) 

    def __get_delivery_data(self) -> Tuple[TradeGood, int]:
        return self.order.good, min(self.order.units_picked_up-self.order.units_delivered, self.navigable.ship.cargo.get_item_count(self.order.good.symbol))

    def __get_delivery_location(self):
        if not self.order:
            return None
        if self.order.delivery_ship:
            return self.order.delivery_wp, self.order.delivery_ship.nav.live_status
        return self.order.delivery_wp, ShipNavStatus.DOCKED

    def order_deliver(self, units: int):
        self.order.units_delivered += units

    def on_enter(self):
        self.order = self.get_order()
        if x := self.__get_delivery_location():
            self.navigable.set_destination(x[0], x[1])
        return super().on_enter()
