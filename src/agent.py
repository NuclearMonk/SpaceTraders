from login import API_KEY
from utils import print_json
from requests import get


AGENT_BASE_URL = 'https://api.spacetraders.io/v2/my/agent'

def get_agent_data():
    headers = {"Authorization": f"Bearer {API_KEY}"}
    response = get(AGENT_BASE_URL,headers=headers)
    if response.ok:
        return response.json()
    else:
        return None
    
if __name__ == "__main__":
    print_json(get_agent_data())