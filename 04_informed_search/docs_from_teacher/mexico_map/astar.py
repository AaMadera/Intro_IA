"""A* search for the Mexican city graph."""

from __future__ import annotations

import heapq
from collections.abc import Callable

from search.result import FAILURE, SUCCESS, SearchResult

from .node import Node
from .problem import RouteFindingProblem


def a_star_search(
    problem: RouteFindingProblem, h: Callable[[int], float]
) -> SearchResult:
    node = Node(problem.start)
    frontier: list[tuple[float, int, Node]] = []
    counter = 0
    heapq.heappush(frontier, (node.path_cost + h(node.state), counter, node))
    best_g = {node.state: 0.0}
    explored: set[int] = set()
    expanded = 0
    generated = 1
    max_frontier = 1

    while frontier:
        _f, _i, node = heapq.heappop(frontier)
        if node.state in explored:
            continue
        if problem.is_goal(node.state):
            return SearchResult(
                SUCCESS,
                node,
                nodes_expanded=expanded,
                nodes_generated=generated,
                max_frontier=max_frontier,
            )

        explored.add(node.state)
        expanded += 1
        for child in node.expand(problem):
            generated += 1
            state = child.state
            if state in explored:
                continue
            if state not in best_g or child.path_cost < best_g[state]:
                best_g[state] = child.path_cost
                counter += 1
                heapq.heappush(frontier, (child.path_cost + h(state), counter, child))
                max_frontier = max(max_frontier, len(frontier))

    return SearchResult(
        FAILURE,
        nodes_expanded=expanded,
        nodes_generated=generated,
        max_frontier=max_frontier,
    )
