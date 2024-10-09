from typing import List, Optional

from pydantic import TypeAdapter
from sqlalchemy import select
from crud.tradegood import get_good
from crud.waypoint import get_waypoint_with_symbol
from login import HEADERS, SYSTEM_BASE_URL, CONTRACTS_BASE_URL, engine, get
from models.contract import ContractDeliveryModel, ContractModel
from schemas.contract import Contract, ContractDelivery, ContractPayment, ContractTerms
from sqlalchemy.orm import Session


def store_contract(contract: Contract):
    with Session(engine) as session:
        if db_contract := _get_contract_from_db(id, session):
            _update_contract_in_db(db_contract, contract)
        else:
            _store_contract_in_db(contract, session)


def get_contract_with_id(id: str):
    with Session(engine) as session:
        if contract := _get_contract_from_db(id, session):
            return _record_to_schema(contract)
        fresh_contract = _get_contract_from_server(id)
        contract = _record_to_schema(
            _store_contract_in_db(fresh_contract, session))
        return contract


def get_all_contracts():
    with Session(engine) as session:
        return [_record_to_schema(c) for c in session.scalars(select(ContractModel)).all()]


def get_open_contracts():
    with Session(engine) as session:
        return [_record_to_schema(c) for c in session.scalars(select(ContractModel).where(ContractModel.fulfilled == False)).all()]


def update_contract(contract: Contract):
    with Session(engine) as session:
        if db_contract := _get_contract_from_db(contract.id, session):
            _update_contract_in_db(db_contract, contract)
        else:
            _store_contract_in_db(contract, session)


def refresh_contract_cache():
    contracts = _get_all_contracts_from_server()
    with Session(engine) as session:
        for contract in contracts:
            if db_contract := _get_contract_from_db(contract.id, session):
                _update_contract_in_db(db_contract, contract, session)
            else:
                _store_contract_in_db(contract, session)


def _get_all_contracts_from_server(limit=20):
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


def _record_to_schema(contract: ContractModel) -> Contract:
    if not contract:
        return None
    return Contract(
        id=contract.id,
        factionSymbol=contract.faction_symbol,
        type=contract.contract_type,
        terms=ContractTerms(deadline=contract.terms_deadline,
                            payment=ContractPayment(
                                onAccepted=contract.terms_pay_accepted,
                                onFulfilled=contract.terms_pay_fulfilled),
                            deliver=[_get_contract_delivery(
                                delivery) for delivery in contract.deliver]
                            ),
        accepted=contract.accepted,
        fulfilled=contract.fulfilled,
        deadlineToAccept=contract.deadline_to_accept
    )


def _update_contract_in_db(db_contract: ContractModel, contract: Contract, session: Session) -> ContractModel:
    print("updating contract")
    db_contract.accepted = contract.accepted
    db_contract.fulfilled = contract.fulfilled
    for delivery in contract.terms.deliver:
        session.scalars(select(
            ContractDeliveryModel).where(
                ContractDeliveryModel.contract_id == contract.id and
            ContractDeliveryModel.trade_symbol == delivery.tradeSymbol)).first().fulfilled = delivery.unitsFulfilled
    session.commit()
    return db_contract


def _store_contract_in_db(contract: Contract, session: Session) -> ContractModel:
    new_contract = ContractModel()
    new_contract.id = contract.id
    new_contract.faction_symbol = contract.factionSymbol
    new_contract.contract_type = contract.contract_type
    new_contract.terms_deadline = contract.terms.deadline
    new_contract.terms_pay_accepted = contract.terms.payment.onAccepted
    new_contract.terms_pay_fulfilled = contract.terms.payment.onFulfilled
    new_contract.deliver = [_store_delivery(
        delivery, session) for delivery in contract.terms.deliver]
    new_contract.accepted = contract.accepted
    new_contract.fulfilled = contract.fulfilled
    new_contract.deadline_to_accept = contract.deadlineToAccept
    session.add(new_contract)
    session.commit()
    return new_contract


def _get_contract_from_server(id: str) -> Optional[Contract]:
    response = get(f"{CONTRACTS_BASE_URL}/{id}", headers=HEADERS)
    if response.ok:
        js = response.json()
        return Contract.model_validate(js["data"])
    else:
        return None


def _get_contract_from_db(id: str, session: Session):
    return session.scalars(select(ContractModel).where(ContractModel.id == id)).first()


def _store_delivery(delivery: ContractDelivery, session: Session) -> ContractDeliveryModel:
    model = ContractDeliveryModel()
    model.trade_symbol = delivery.tradeSymbol
    model.delivery_symbol = delivery.destinationSymbol
    model.required = delivery.unitsRequired
    model.fulfilled = delivery.unitsFulfilled
    session.commit()
    return model


def _get_contract_delivery(model: ContractDeliveryModel) -> ContractDelivery:
    return ContractDelivery(
        tradeSymbol=model.trade_symbol,
        destinationSymbol=model.delivery_symbol,
        unitsRequired=model.required,
        unitsFulfilled=model.fulfilled
    )
