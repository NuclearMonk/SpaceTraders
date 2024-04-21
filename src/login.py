from requests_ratelimiter import LimiterSession
from sqlalchemy import create_engine
from utils.utils import print_json
from pathlib import Path
from os import path


REGISTER_URL = 'https://api.spacetraders.io/v2/register'
SYSTEM_BASE_URL = "https://api.spacetraders.io/v2/systems/"
CREDENTIALS_PATH = Path("data/apikey")
USERNAME = "shocsoares"
FACTION = "VOID"


def register_request(username, faction):
    register_data = {"symbol": username,
                     "faction": faction}
    return post(REGISTER_URL, json=register_data)


def store_api_key(key):
    if not path.exists(CREDENTIALS_PATH):
        with open(CREDENTIALS_PATH, "w")as f:
            f.write(key)


def get_api_key():
    if path.exists(CREDENTIALS_PATH):
        with open(CREDENTIALS_PATH) as f:
            return f.read().strip()
    else:
        print("API KEY FILE  NOT FOUND")
        return None


def register():
    response = register_request(USERNAME, FACTION)
    if response.ok:
        data = response.json()
        print_json(data)
        print("REGISTER SUCCESS")
        store_api_key(data["data"]["token"])
    else:
        print_json(data)
        print("REGISTER FAILED")


if __name__ == "__main__":
    register()
else:
    
    engine =  create_engine('sqlite:///data/test.db')
    HEADERS = get_api_key()
    HEADERS = {"Authorization": f"Bearer {HEADERS}"}
    session = LimiterSession(per_second=2)
    get = session.get
    post = session.post
    patch = session.patch
