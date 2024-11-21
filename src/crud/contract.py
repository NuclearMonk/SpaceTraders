
from datetime import UTC
from logging import getLogger
from sqlalchemy import select
from login import engine
from models.contract import ContractDeliveryModel, ContractModel
from schemas.contract import Contract, ContractDelivery, ContractPayment, ContractTerms
from sqlalchemy.orm import Session

logger = getLogger(__name__)


def create_update_contract(contract: Contract) -> Contract:
    with Session(engine) as session:
        if db_contract := _get_contract_from_db(contract.id, session):
            return _contract_to_schema(_update_contract_in_db(db_contract, contract, session))
        return _contract_to_schema(_store_contract_in_db(contract, session))


def get_contract_from_db(id: str) -> Contract:
    logger.info(f"getting contract from db with id: {id}")
    with Session(engine) as session:
        return _contract_to_schema(_get_contract_from_db(id, session))


def get_open_contracts_db():
    with Session(engine) as session:
        return [_contract_to_schema(c) for c in session.scalars(select(ContractModel).where(ContractModel.fulfilled == False))]


def _contract_to_schema(contract: ContractModel) -> Contract:
    if not contract:
        return None
    return Contract(
        id=contract.id,
        factionSymbol=contract.faction_symbol,
        type=contract.contract_type,
        terms=ContractTerms(deadline=contract.terms_deadline.replace(tzinfo=UTC),
                            payment=ContractPayment(
                                onAccepted=contract.terms_pay_accepted,
                                onFulfilled=contract.terms_pay_fulfilled),
                            deliver=[ContractDelivery(tradeSymbol=delivery.trade_symbol,
                                                      destinationSymbol=delivery.delivery_symbol,
                                                      unitsRequired=delivery.required,
                                                      unitsFulfilled=delivery.fulfilled) for delivery in contract.deliver]
                            ),
        accepted=contract.accepted,
        fulfilled=contract.fulfilled,
        deadlineToAccept=contract.deadline_to_accept.replace(tzinfo=UTC)
    )


def _update_contract_in_db(db_contract: ContractModel, contract: Contract, session: Session) -> ContractModel:
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


def _get_contract_from_db(id: str, session: Session):
    return session.scalars(select(ContractModel).where(ContractModel.id == id)).first()


def _store_delivery(delivery: ContractDelivery, session: Session) -> ContractDeliveryModel:
    d = ContractDeliveryModel()
    d.trade_symbol = delivery.tradeSymbol
    d.delivery_symbol = delivery.destinationSymbol
    d.required = delivery.unitsRequired
    d.fulfilled = delivery.unitsFulfilled
    session.add(d)
    return d
