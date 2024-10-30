
from crud.request import store_request, store_response
from login import get
from login import HEADERS

def get_request(url):
    id = store_request('GET',url)
    resp =get(url, headers=HEADERS)
    store_response(id, resp.status_code, resp.text)
    return resp
