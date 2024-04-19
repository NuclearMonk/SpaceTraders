from login import HEADERS,get, post
from utils.utils import print_json
import argparse

CONTRACTS_BASE_URL = 'https://api.spacetraders.io/v2/my/contracts/'


def get_contract_data():
    headers = {"Authorization": f"Bearer {HEADERS}"}
    response = get(CONTRACTS_BASE_URL, headers=headers)
    if response.ok:
        return response.json()
    else:
        return None


def accept_contract(id):
    headers = {"Authorization": f"Bearer {HEADERS}"}
    response = post(CONTRACTS_BASE_URL+id + "/accept", headers=headers)
    if response.ok:
        return response.json()
    else:
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--accept")
    args = parser.parse_args()
    if args.accept:
        print(f"Accepting contract: {args.accept}")
        print_json(accept_contract(args.accept))
    else:
        print_json(get_contract_data())
