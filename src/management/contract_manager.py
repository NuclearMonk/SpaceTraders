

from typing import Dict, List, Optional
from crud.job import assign_job
from crud.tradegood import get_good
from management.job import JobAssignment
from management.negotiator import Negotiator
from management.transport_manager import TransportManager, TransportOrder
from schemas.contract import Contract
from schemas.ship import Ship
from st_requests.contract import get_all_contracts_from_server, get_open_contracts
from st_requests.market import get_markets_exporting
from st_requests.waypoint import get_waypoint


class ContractManager:

    def __init__(self, negotiator: Ship, transport_manager: TransportManager) -> None:
        self.negotiator = Negotiator(negotiator, self.request_pickup,self.get_contract, self.set_contract)
        assign_job(negotiator, JobAssignment.CONTRACT_NEGOTIATOR)
        get_all_contracts_from_server()
        self.contract = None
        if contracts := get_open_contracts():
                self.contract = contracts[0]
        self.transport_manager = transport_manager


    def do_cycle(self) -> bool:
        return self.negotiator.do_tick()
    
    def get_contract(self)-> Optional[Contract]:
        return self.contract
    
    def set_contract(self,contract:Contract):
        self.contract = contract

    def request_pickup(self,contract: Contract):
        for delivery in contract.terms.deliver:
            good = get_good(delivery.tradeSymbol)
            delivery_wp = get_waypoint(delivery.destinationSymbol)
            if not delivery_wp:
                return 
            markets = sorted(get_markets_exporting(delivery.tradeSymbol), key=lambda m: delivery_wp.distance_to(get_waypoint(m.symbol)))
            if not markets:
                return
            pickup_wp = get_waypoint(markets[0].symbol)
            units = delivery.unitsRequired - delivery.unitsFulfilled
            self.transport_manager.add_transport_order(TransportOrder(good,
                           units,
                           pickup_wp,
                           delivery_wp,contract=contract))