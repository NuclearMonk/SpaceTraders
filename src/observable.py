

from typing import List, Callable


class Observable():
    _observers: List[Callable] = []

    def update(self):
        for observer in self._observers:
            observer(self)

    def add_observer(self, f: Callable) -> None:
        self._observers.append(f)

    def remove_observer(self, f: Callable) -> None:
        self._observers.remove(f)
