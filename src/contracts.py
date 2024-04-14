from login import API_KEY
from utils import print_json
from requests import get, post
import argparse

CONTRACTS_BASE_URL = 'https://api.spacetraders.io/v2/my/contracts/'


def get_contract_data():
    headers = {"Authorization": f"Bearer {API_KEY}"}
    response = get(CONTRACTS_BASE_URL, headers=headers)
    if response.ok:
        return response.json()
    else:
        return None


def accept_contract(id):
    headers = {"Authorization": f"Bearer {API_KEY}"}
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
