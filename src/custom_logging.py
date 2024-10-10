import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Callable


def create_ship_logger(ship_symbol: str) -> Callable[[str], None]:
    log_file = Path("data", "logs", "ships", f"{ship_symbol}.log")
    handler = logging.FileHandler(log_file)
    logger = logging.getLogger(ship_symbol)
    logger.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter(
        fmt='%(asctime)s|%(name)s%(message)s',
        datefmt='%m/%d/%Y %I:%M:%S %p'))

    logger.addHandler(handler)
    return logger
