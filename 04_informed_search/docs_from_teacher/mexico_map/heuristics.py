"""Haversine heuristic for the Mexico city graph."""

from __future__ import annotations

import math
from collections.abc import Callable

from .graph import MexicoGraph

EARTH_RADIUS_KM = 6371.0


def haversine(graph: MexicoGraph, source: int, target: int) -> float:
    lat1, lon1 = graph.coordinates(source)
    lat2, lon2 = graph.coordinates(target)
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    value = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(min(1.0, value)))


def heuristic_for(graph: MexicoGraph, goal: int) -> tuple[Callable[[int], float], str]:
    def h(state: int) -> float:
        return haversine(graph, state, goal)

    return h, f"straight-line distance to {graph.name(goal)} (haversine)"
