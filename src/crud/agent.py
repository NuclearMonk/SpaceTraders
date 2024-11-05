from sqlalchemy.orm import Session


from crud.waypoint import _get_waypoint
from models.agent import AgentModel
from schemas.agent import Agent
from login import engine


def _agent_to_schema(model: AgentModel) -> Agent:
    return Agent(symbol=model.symbol,
                 headquarters=model.headquarters_symbol,
                 credits=model.credits,
                 startingFaction=model.starting_faction,
                 shipCount=model.ship_count)


def create_agent(agent: Agent) -> Agent:
    with Session(engine) as session:
        model= AgentModel(agent.symbol,
                               _get_waypoint(agent.headquarters, session),
                               agent.credits,
                               agent.startingFaction,
                               agent.shipCount
                               )
        session.add(model)
        session.commit()
        return _agent_to_schema(model)
