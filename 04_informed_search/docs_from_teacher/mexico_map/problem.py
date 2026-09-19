"""Route-finding problem on the Mexican city graph."""

from __future__ import annotations

from .graph import MexicoGraph


class RouteFindingProblem:
    """State = city ID. Action = move to a neighboring city. Cost = km."""

    def __init__(self, graph: MexicoGraph, start: int, goal: int) -> None:
        if not graph.has_city(start):
            raise ValueError(f"unknown start city ID: {start}")
        if not graph.has_city(goal):
            raise ValueError(f"unknown goal city ID: {goal}")
        self.graph = graph
        self.start = start
        self.goal = goal

    def actions(self, state: int) -> list[int]:
        return [city_id for city_id, _km in self.graph.neighbors(state)]

    def result(self, state: int, action: int) -> int:
        return action

    def step_cost(self, state: int, action: int) -> float:
        return self.graph.cost(state, action)

    def is_goal(self, state: int) -> bool:
        return state == self.goal
