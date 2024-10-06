from typing import List, Optional

from pydantic import TypeAdapter
from sqlalchemy import select
from login import HEADERS, SYSTEM_BASE_URL, CONTRACTS_BASE_URL, engine, get
from models.contract import ContractModel
from schemas.contract import Contract, ContractDeliveryGood, ContractPayment, ContractTerms
from sqlalchemy.orm import Session


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

def update_contract(contract: Contract):
    with Session(engine) as session:
        if db_contract := _get_contract_from_db(contract.id, session):
            db_contract.deliver_units_fulfilled = contract.terms.deliver[0].unitsFulfilled
            db_contract.accepted = contract.accepted
            db_contract.fulfilled = contract.fulfilled
            session.commit()
        else:
            _store_contract_in_db(contract, session)

def refresh_cache():
    contracts = _get_all_contracts_from_server()
    with Session(engine) as session:
        for contract in contracts:
            if db_contract := _get_contract_from_db(contract.id, session):
                return _record_to_schema(_update_contract_in_db(db_contract, contract, session))
        _record_to_schema(
            _store_contract_in_db(contract, session))


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
                            deliver=[ContractDeliveryGood(
                                tradeSymbol=contract.deliver_trade_symbol,
                                destinationSymbol=contract.deliver_symbol,
                                unitsRequired=contract.deliver_units_required,
                                unitsFulfilled=contract.fulfilled)]
                            ),
        accepted=contract.accepted,
        fulfilled=contract.fulfilled,
        deadlineToAccept=contract.deadline_to_accept
    )


def _update_contract_in_db(db_contract: ContractModel, contract: Contract, session: Session) -> ContractModel:
    db_contract.accepted = contract.accepted
    db_contract.fulfilled = contract.fulfilled
    db_contract.deliver_units_required = contract.terms.deliver[0].unitsRequired
    db_contract.deliver_units_fulfilled = contract.terms.deliver[0].unitsFulfilled
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
    new_contract.deliver_trade_symbol = contract.terms.deliver[0].tradeSymbol
    new_contract.deliver_symbol = contract.terms.deliver[0].destinationSymbol
    new_contract.deliver_units_required = contract.terms.deliver[0].unitsRequired
    new_contract.deliver_units_fulfilled = contract.terms.deliver[0].unitsFulfilled
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


def _get_contract_from_db(id: str, session):
    return session.scalars(select(ContractModel).where(ContractModel.id == id)).first()
