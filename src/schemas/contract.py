from datetime import datetime
from enum import StrEnum
from logging import getLogger
from typing import List
from pydantic import BaseModel, Field, TypeAdapter, ValidationError
from crud.agent import create_agent
from login import CONTRACTS_BASE_URL, HEADERS, get, post
from schemas.agent import Agent
from schemas.faction import FactionSymbol
from st_requests.request import post_request
from utils.observable import Observable

logger = getLogger(__name__)


class ContractType(StrEnum):
    PROCUREMENT = 'PROCUREMENT'
    TRANSPORT = 'TRANSPORT'
    SHUTTLE = 'SHUTTLE'


class ContractPayment(BaseModel):
    onAccepted: int
    onFulfilled: int


class ContractDelivery(BaseModel):
    tradeSymbol: str
    destinationSymbol: str
    unitsRequired: int
    unitsFulfilled: int


class ContractTerms(BaseModel):
    deadline: datetime
    payment: ContractPayment
    deliver: List[ContractDelivery]


class Contract(BaseModel, Observable):
    id: str
    factionSymbol: FactionSymbol
    contract_type: ContractType = Field(alias='type')
    terms: ContractTerms
    accepted: bool
    fulfilled: bool
    deadlineToAccept: datetime

    def __init__(self,  **kwargs):
        super().__init__(**kwargs)

    @property
    def ready_to_fulfill(self) -> bool:
        for delivery in self.terms.deliver:
            if delivery.unitsFulfilled < delivery.unitsRequired:
                return False
        return True

    def accept(self) -> bool:
        response = post_request(f'{CONTRACTS_BASE_URL}/{self.id}/accept')
        if not response.ok:
            logger.warning("Accept Contract Request Failed")
            return self.accepted
        js = response.json()
        try:
            agent = Agent.model_validate(js['data']['agent'])
            create_agent(agent)
            contract = Contract.model_validate(js['data']['contract'])
            self.accepted = contract.accepted
            self.update()
            return self.accepted
        except ValidationError as e:
            self.log(f'Validation Failed', error=True)
            return self.accepted

    def fulfill(self) -> bool:
        response = post_request(f'{CONTRACTS_BASE_URL}/{self.id}/fulfill')
        if not response.ok:
            logger.warning("Fullfil Contract Request Failed")
            return self.fulfilled
        js = response.json()
        try:
            agent = Agent.model_validate(js['data']['agent'])
            create_agent(agent)
            contract = Contract.model_validate(js['data']['contract'])
            self.fulfilled = contract.fulfilled
            self.update()
            return self.fulfilled
        except ValidationError as e:
            self.log(f'Validation Failed', error=True)
            return self.fulfilled
