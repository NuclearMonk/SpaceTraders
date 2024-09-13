from login import HEADERS, get
from utils.utils import print_json


AGENT_BASE_URL = 'https://api.spacetraders.io/v2/my/agent'


def get_agent_data():
    response = get(AGENT_BASE_URL, headers=HEADERS)
    if response.ok:
        return response.json()
    else:
        return None


if __name__ == "__main__":
    print_json(get_agent_data())
