
from typing import Optional
from sqlalchemy.orm import Session


from login import engine
from models.request import RequestModel, ResponseModel


def store_request(method: str, url: str, body: Optional[str]= None) -> int:
    with Session(engine) as session:
        req = RequestModel()
        req.method = method
        req.url = url
        req.body = body
        session.add(req)
        session.commit()
        return req.id


def store_response(req_id: int, code: int, body: str):
    with Session(engine) as session:
        res = ResponseModel()
        res.id = req_id
        res.code = code
        res.body = body
        session.add(res)
        session.commit()
