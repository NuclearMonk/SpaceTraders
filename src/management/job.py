

from enum import Enum


class JobAssignment(str, Enum):
    MINING_DRONE = "Mining Drone"
    HAULER = "Hauler"
    CONTRACT_NEGOTIATOR = "Contract Negotiator"
    IDLE = "Idle"
