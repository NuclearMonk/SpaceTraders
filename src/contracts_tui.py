from login import CONTRACTS_BASE_URL, HEADERS,get, post
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
    args = parser.parse_args()
    if args.accept:
        print(f"Accepting contract: {args.accept}")
        print_json(accept_contract(args.accept))
    if args.fulfill:
        print(f"Fulfilling contract: {args.fulfill}")
        print_json(fulfill_contract(args.fulfill))
    else:
        print_json(get_contract_data())
