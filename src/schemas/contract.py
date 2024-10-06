from datetime import datetime
from enum import StrEnum
from typing import List
from pydantic import BaseModel, Field, TypeAdapter
from login import CONTRACTS_BASE_URL, HEADERS, get, post


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
    terms: ContractTerms
    accepted: bool
    fulfilled: bool
    deadlineToAccept: datetime

    def accept(self):
        print(f"Accepting {self.id}")
        self.accepted = post(
            f"{CONTRACTS_BASE_URL}/{self.id}/accept", headers=HEADERS).ok
        print(self.accepted)
        return self.accepted

    def fulfill(self):
        self.fulfilled = post(
            f"{CONTRACTS_BASE_URL}/{self.id}/fulfill", headers=HEADERS).ok
        return self.fulfilled


def get_contract(id: str):
    response = get(f"{CONTRACTS_BASE_URL}/{id}", headers=HEADERS)
    if response.ok:
        print(response.json())
        return Contract.model_validate(response.json()["data"])
    else:
        return None


def get_all_contracts(limit=20):
    contracts: list[Contract] = []
    ta = TypeAdapter(List[Contract])
    current = 0
    m = float("inf")
    page = 1
    while current < m:
        response = get(CONTRACTS_BASE_URL +
                       f"?page={page}&limit={limit}", headers=HEADERS)
        if response.ok:
            js = response.json()
            m = js["meta"]["total"]
            current += len(js["data"])
            page += 1
            new_contracts = ta.validate_python(js["data"])
            contracts.extend(new_contracts)
    return contracts


# def get_open_contracts() -> List[Contract]:
#     return [contract for contract in get_all_contracts() if not contract.fulfilled]
