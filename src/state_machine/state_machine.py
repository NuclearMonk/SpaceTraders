from typing import Any, Callable, Dict, List, Tuple, override
from graphviz import Digraph


class State:

    def __init__(self, name) -> None:
        self.name = name

    def get_name(self) -> str:
        return self.name

    def on_enter(self) -> bool:
        pass

    def on_exit(self) -> bool:
        pass

    def do_tick(self) -> bool:
        return False

    def __str__(self) -> str:
        return self.name

    def viz(self, graph: Digraph):
        return graph.node(self.name, label=self.name)


class Transition:

    def __init__(self, origin_key: str, destination_key: str, condition: Callable[[], bool], description: str) -> None:
        self.origin_key = origin_key
        self.destination_key = destination_key
        self.condition = condition
        self.description = description

    def test_condition(self) -> bool:
        return self.condition()

    def __str__(self) -> str:
        return f"{self.origin_key}->{self.destination_key}: {self.description}"

    def viz(self, graph: Digraph):
        graph.edge(self.origin_key, self.destination_key, self.description)


class StateMachine(State):
    def __init__(self, name, states: List[State], trans: List[Transition], entry_state: str) -> None:
        self.name = name
        self.states: Dict[str, State] = {state.name: state for state in states}
        self.transitions: List[Transition] = trans
        self.entry_state = entry_state
        self.current_state = None
        self.set_state(entry_state)

    def __str__(self) -> str:
        return f"{self.name}>{self.current_state}"

    def set_state(self, state_name: str):
        if self.current_state:
            self.current_state.on_exit()
        self.current_state = self.states[state_name]
        self.current_state.on_enter()

    @override
    def on_enter(self):
        self.set_state(self.entry_state)

    @override
    def on_exit(self):
        if self.current_state:
            self.current_state.on_exit()
        self.current_state = None

    @override
    def do_tick(self) -> bool:
        for trans in self.transitions:
            if trans.origin_key == self.current_state.get_name() and trans.test_condition():
                self.set_state(trans.destination_key)
                break
        return self.current_state.do_tick()

    def viz(self, graph=None):
        if not graph:
            graph = Digraph()
        g = Digraph("cluster " +self.name, graph_attr={'style':'filled'}, node_attr={'shape': 'circle'})
        g.node(self.name)
        for state in self.states.values():
            state.viz(g)
        g.edge(self.name, self.entry_state  )    
        for trans in self.transitions:
            trans.viz(g)
        graph.subgraph(g)
        return graph
