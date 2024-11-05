

from typing import List, Optional

from pydantic import TypeAdapter

from crud.contract import create_update_contract, get_contract_from_db, get_open_contracts_db
from schemas.meta import Meta
from schemas.contract import Contract
from logging import getLogger

from st_requests.request import get_request
from st_requests.waypoint import get_waypoint

CONTRACTS_BASE_URL = 'https://api.spacetraders.io/v2/my/contracts/'
logger = getLogger(__name__)


def __get_contract_from_server(id: str) -> Optional[Contract]:
    logger.info(f"getting contract from server with id: {id}")
    response = get_request(f'{CONTRACTS_BASE_URL}/{id}')
    if not response.ok:
        logger.warning("Get Contract Failed")
        return None
    js = response.json()
    contract = Contract.model_validate(js['data'])
    for delivery in contract.terms.deliver:
        get_waypoint(delivery.destinationSymbol)
    create_update_contract(contract)
    return contract


def get_all_contracts_from_server():
    '''gets all the contracts from the server then\n
    updates them in the local database, then returns them'''

    contracts: List[Contract] = []
    ta = TypeAdapter(List[Contract])
    current = 0
    total = float('inf')
    page = 1
    limit = 20

    while current < total:
        logger.info(f"Getting all contracts({current} out of {total})")
        params = {'page': page, 'limit': limit}
        response = get_request(CONTRACTS_BASE_URL, params=params)
        if not response and not response.ok:
            logger.warning("Get Contract request failed")
            break
        js = response.json()
        meta = Meta.model_validate(js['meta'])
        total = meta.total
        current += len(js['data'])
        page = meta.page+1
        new_ships = ta.validate_python(js['data'])
        contracts.extend(new_ships)
    fancy_contracts = []
    for contract in contracts:
        for delivery in contract.terms.deliver:
            get_waypoint(delivery.destinationSymbol)
        fancy_contracts.append(create_update_contract(contract))
    return fancy_contracts


def get_contract(id: str) -> Optional[Contract]:
    '''gets contract from the database\n
    if not in database then gets from server\n
    updates database\n
    then returns it'''
    logger.info(f"getting contract with id: {id}")
    if contract := get_contract_from_db(id):
        return contract
    return __get_contract_from_server(id)


def get_open_contracts() -> List[Contract]:
    logger.info(f"getting open contracts ")

    return get_open_contracts_db()
