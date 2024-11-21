from typing import List, Callable


class Observable():

    def update(self):
        if not hasattr(self, "_observers"):
            return
        for observer in self._observers:
            observer(self)

    def add_observer(self, f: Callable) -> None:
        if not hasattr(self, "_observers"):
            self._observers: List[Callable] = list()
        self._observers.append(f)

    def remove_observer(self, f: Callable) -> None:
        if not hasattr(self, "_observers"):
            return
        self._observers.remove(f)
