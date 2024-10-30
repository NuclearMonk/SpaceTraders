

from crud.agent import create_agent
from .request import get_request
from schemas.agent import Agent


AGENT_URL = 'https://api.spacetraders.io/v2/my/agent'


def get_my_agent() -> Agent:
    response = get_request(AGENT_URL)
    data = response.json()['data']
    agent = Agent.model_validate(data)
    create_agent(agent)
    return agent
