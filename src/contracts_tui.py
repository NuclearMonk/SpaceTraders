from login import CONTRACTS_BASE_URL, HEADERS,get, post
from schemas.contract import get_all_contracts, get_open_contracts
from utils.utils import print_json
import argparse



def get_contract_data():
    response = get(CONTRACTS_BASE_URL, headers=HEADERS)
    if response.ok:
        return response.json()
    else:
        return None

def fulfill_contract(id):
    response = post(f"{CONTRACTS_BASE_URL}/{id}/fulfill", headers=HEADERS)
    print(response)
    if response.ok:
        return response.json()
    else:
        return None

def accept_contract(id):
    response = post(f"{CONTRACTS_BASE_URL}/{id}/accept", headers=HEADERS)
    print(response)
    if response.ok:
        return response.json()
    else:
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--accept")
    parser.add_argument("-f", "--fulfill")
    parser.add_argument("-o", "--open", action="store_true")
    args = parser.parse_args()
    if args.accept:
        print(f"Accepting contract: {args.accept}")
        print_json(accept_contract(args.accept))
    if args.fulfill:
        print(f"Fulfilling contract: {args.fulfill}")
        print_json(fulfill_contract(args.fulfill))
    if args.open:
        for contract in get_open_contracts():
            print(contract.model_dump_json(indent=2))       
    else:
        for contract in get_all_contracts():
            print(contract.model_dump_json(indent=2))
