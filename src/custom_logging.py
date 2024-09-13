from logging.handlers import RotatingFileHandler
from pathlib import Path

def create_ship_logger(ship_symbol: str)-> callable(str):
    log_file = Path("data", "logs", f"{ship_symbol}.log")
    open(log_file,"a").close()