

from typing import Dict, List
from crud.job import assign_job
from crud.tradegood import get_good
from management.job import JobAssignment
from management.transport_manager import TransportManager, TransportOrder
from schemas.contract import Contract
from schemas.ship import Ship
from st_requests.contract import get_all_contracts_from_server, get_open_contracts
from st_requests.market import get_markets_exporting
from st_requests.waypoint import get_waypoint


class ContractManager:

    def __init__(self, negotiator: Ship, transport_manager: TransportManager) -> None:
        self.negotiator = negotiator
        assign_job(negotiator, JobAssignment.CONTRACT_NEGOTIATOR)
        get_all_contracts_from_server()
        self.contract = None
        self.transport_manager = transport_manager
        self.contracts_assigned: Dict[str, bool] = {}

    def do_cycle(self) -> bool:
        if not self.contract:
            if contracts := get_open_contracts():
                self.contract = contracts[0]
                return True
            success, contract = self.negotiator.negotiate_contract()
            if success:
                self.contract = contract
                return True
            return False
        if not self.contract.accepted:
            self.contract.accept()
            return True
        if self.contract.ready_to_fulfill:
            if self.contract.fulfill():
                self.contracts_assigned[self.contract.id] = True
                self.contract = None
                return True

        if not self.contracts_assigned.get(self.contract.id, False):
            for delivery in self.contract.terms.deliver:
                wps = [get_waypoint(m.symbol)
                       for m in get_markets_exporting(delivery.tradeSymbol)]
                if not wps:
                    return False
                delivery_wp = get_waypoint(delivery.destinationSymbol)
                wps.sort(key=lambda x: delivery_wp.distance_to(x))
                pickup_wp = wps[0]
                to = TransportOrder(get_good(delivery.tradeSymbol),
                                    delivery.unitsRequired-delivery.unitsFulfilled,
                                    pickup_wp,
                                    delivery_wp, contract=self.contract)
                print(to)
                self.transport_manager.add_transport_order(to)
                self.contracts_assigned[self.contract.id] = True
        return False
