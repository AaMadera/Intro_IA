#!/usr/bin/env python3

"""Run A* search on the generated Mexico city graph."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from mexico_map.astar import a_star_search
from mexico_map.cli import make_problem, print_result, search_parser
from mexico_map.heuristics import heuristic_for


def main() -> None:
    parser = search_parser("A* search: expand lowest f(n) = g(n) + h(n).")
    args = parser.parse_args()
    graph, problem, warnings = make_problem(
        args.start_city, args.goal_city, args.start_state, args.goal_state
    )
    h, label = heuristic_for(graph, problem.goal)
    result = a_star_search(problem, h)
    print_result("A* search", graph, problem, result, h, label, warnings)


if __name__ == "__main__":
    main()
