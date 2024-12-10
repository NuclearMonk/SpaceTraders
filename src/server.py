from flask import Flask
from markupsafe import escape

from crud.ship import get_ship

app = Flask(__name__)

@app.route("/ship/<symbol>")
def ship(symbol):
    symbol = symbol
    ship = get_ship(symbol)
    return ship.model_dump_json()