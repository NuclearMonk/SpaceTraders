

from schemas.contract import Contract


class ManagedContract():

    def __init__(self, contract: Contract) -> None:
        self.contract = contract
        