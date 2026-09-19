"""CLI helpers for Mexico graph searches."""

from __future__ import annotations

import argparse
from collections.abc import Callable

from search.result import SearchResult

from .graph import MexicoGraph
from .node import Node
from .problem import RouteFindingProblem

GRAPH_PATH = (
    __import__("pathlib").Path(__file__).resolve().with_name("mexico_cities_graph.json")
)


def search_parser(description: str) -> argparse.ArgumentParser:
    # It was found some cities that are repeated in different states
    # E.G. Puebla, Puebla and Puebla, Baja California
    # So passing the states is optional but recommended
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--from-city", dest="start_city", required=True, help="Starting city name"
    )
    parser.add_argument(
        "--from-state", dest="start_state", help="State for an ambiguous starting city"
    )
    parser.add_argument(
        "--to-city", dest="goal_city", required=True, help="Goal city name"
    )
    parser.add_argument(
        "--to-state", dest="goal_state", help="State for an ambiguous goal city"
    )
    return parser


def make_problem(
    start: str, goal: str, start_state: str | None = None, goal_state: str | None = None
):
    graph = MexicoGraph(GRAPH_PATH)
    start_id = graph.find_city(start, start_state)
    goal_id = graph.find_city(goal, goal_state)
    warnings = []
    if len(graph.city_matches(start)) > 1 and start_state:
        warnings.append(
            f"Origin {start!r} was disambiguated with state {start_state!r}."
        )
    if len(graph.city_matches(goal)) > 1 and goal_state:
        warnings.append(
            f"Destination {goal!r} was disambiguated with state {goal_state!r}."
        )
    return graph, RouteFindingProblem(graph, start_id, goal_id), warnings


def print_result(
    name: str,
    graph: MexicoGraph,
    problem: RouteFindingProblem,
    result: SearchResult,
    h: Callable[[int], float],
    h_label: str,
    warnings: list[str] | None = None,
) -> None:
    print(f"Algorithm: {name}")
    print(
        f"Problem:   {graph.name(problem.start)} ({graph.state(problem.start)}) → {graph.name(problem.goal)} ({graph.state(problem.goal)})"
    )
    print(f"Heuristic: {h_label}")
    for warning in warnings or []:
        print(f"Notice:    {warning}")
    print(f"Status:    {result.status}")
    if result.node is not None:
        path = [f"{graph.name(city)} ({graph.state(city)})" for city in result.path]
        print(f"Path:      {' → '.join(path)}")
        print(f"Depth:     {result.depth} roads")
        print(f"Cost:      {result.cost:.2f} km")
        print()
        print("  city                                      g       h       f")
        for city, g, hv, f in _g_h_f_along(result.node, graph, h):
            print(f"  {city:<40} {g:7.2f} {hv:7.2f} {f:7.2f}")
    print()
    print(f"Expanded:  {result.nodes_expanded} nodes")
    print(f"Generated: {result.nodes_generated} nodes")
    print(f"Frontier:  max size {result.max_frontier}")


def _g_h_f_along(
    node: Node, graph: MexicoGraph, h: Callable[[int], float]
) -> list[tuple[str, float, float, float]]:
    rows = []
    for city in node.path():
        hv = h(city)
        rows.append(
            (
                f"{graph.name(city)} ({graph.state(city)})",
                _path_cost(node, city),
                hv,
                _path_cost(node, city) + hv,
            )
        )
    return rows


def _path_cost(node: Node, state: int) -> float:
    chain: list[Node] = []
    current: Node | None = node
    while current is not None:
        chain.append(current)
        current = current.parent
    for current in reversed(chain):
        if current.state == state:
            return current.path_cost
    raise ValueError(f"state {state} is not in result path")
