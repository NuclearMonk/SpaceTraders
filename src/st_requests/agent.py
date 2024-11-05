

from crud.agent import create_agent
from crud.waypoint import create_update_waypoint
from st_requests.waypoint import get_waypoint
from .request import get_request
from schemas.agent import Agent


AGENT_URL = 'https://api.spacetraders.io/v2/my/agent'


def get_my_agent() -> Agent:
    response = get_request(AGENT_URL)
    data = response.json()['data']
    agent = Agent.model_validate(data)
    create_update_waypoint(get_waypoint(agent.headquarters))
    create_agent(agent)
    return agent
