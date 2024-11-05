
from typing import Any, Dict
from crud.request import store_request, store_response
from login import get, post, patch
from login import HEADERS

from logging import getLogger

logger = getLogger(__name__)


def get_request(url: str, params: Dict[str, Any] = None):
    id = store_request('GET', url, params=str(params))
    logger.debug("Making GET Request with id: {id}")
    resp = get(url, headers=HEADERS, params=params)
    if not resp.ok:
        logger.warning(f"Request {id} failed with code {resp.status_code}")
    store_response(id, resp.status_code, resp.text)
    return resp


def post_request(url: str, data: Dict[str, Any] = None):
    id = store_request('POST', url, body=str(data))
    logger.debug("Making POST Request with id: {id}")
    resp = post(url, headers=HEADERS, data=data)
    if not resp.ok:
        logger.warning(f"Request {id} failed with code {resp.status_code}")
    store_response(id, resp.status_code, resp.text)
    return resp


def patch_request(url: str, data: Dict[str, Any] = None):
    id = store_request('PATCH', url, body=str(data))
    logger.debug("Making POST Request with id: {id}")
    resp = patch(url, headers=HEADERS, data=data)
    if not resp.ok:
        logger.warning(f"Request {id} failed with code {resp.status_code}")
    store_response(id, resp.status_code, resp.text)
    return resp
