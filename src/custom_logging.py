from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Callable

def create_ship_logger(ship_symbol: str)-> Callable[[str], None]:
    log_file = Path("data", "logs","ships", f"{ship_symbol}.log")
    return lambda x : log(log_file, x)

def log(file, msg):
    with open(file, "a") as f:
        f.write(msg)
        f.write("\n")
def create_logger(name: str)-> Callable[[str], None]:
    log_file = Path("data", "logs", f"{name}.log")
    return open(log_file, "a").write