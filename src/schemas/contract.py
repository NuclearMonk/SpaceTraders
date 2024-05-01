from datetime import datetime
from enum import StrEnum
from typing import List
from pydantic import BaseModel, Field
from login import CONTRACTS_BASE_URL, HEADERS, get

class ContractType(StrEnum):
    PROCUREMENT = "PROCUREMENT"
    TRANSPORT = "TRANSPORT"
    SHUTTLE = "SHUTTLE"


class ContractPayment(BaseModel):
    onAccepted: int
    onFulfilled: int


class ContractDeliveryGood(BaseModel):
    tradeSymbol: str
    destinationSymbol: str
    unitsRequired: int
    unitsFulfilled: int


class ContractTerms(BaseModel):
    deadline: datetime
    payment: ContractPayment
    deliver: List[ContractDeliveryGood]


class Contract(BaseModel):
    id: str
    factionSymbol: str
    contract_type: ContractType = Field(alias="type")
    terms : ContractTerms
    accepted: bool
    fulfilled : bool
    deadlineToAccept: datetime


def get_contract(id:str):
    response = get(f"{CONTRACTS_BASE_URL}/{id}", headers=HEADERS)
    if response.ok:
        print(response.json())
        return Contract.model_validate(response.json()["data"])
    else:
        return None