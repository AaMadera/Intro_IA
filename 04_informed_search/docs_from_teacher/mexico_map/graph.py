"""Weighted graph loaded from the generated Mexico city graph JSON."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path


class MexicoGraph:
    """Undirected graph whose states are numeric node IDs."""

    def __init__(self, graph_path: Path) -> None:
        payload = json.loads(graph_path.read_text(encoding="utf-8"))
        self._nodes = {node["id"]: node for node in payload["nodes"]}
        self._adj: dict[int, dict[int, float]] = defaultdict(dict)
        for edge in payload["edges"]:
            source, target = edge["source"], edge["target"]
            self._adj[source][target] = edge["km"]
            self._adj[target][source] = edge["km"]
        # print(self._adj)

    def has_city(self, city_id: int) -> bool:
        return city_id in self._nodes

    def neighbors(self, city_id: int) -> list[tuple[int, float]]:
        return sorted(self._adj[city_id].items())

    def cost(self, source: int, target: int) -> float:
        if target not in self._adj[source]:
            raise KeyError(f"no edge between {source} and {target}")
        return self._adj[source][target]

    def name(self, city_id: int) -> str:
        return self._nodes[city_id]["name"]

    def state(self, city_id: int) -> str:
        return self._nodes[city_id]["state"]

    def coordinates(self, city_id: int) -> tuple[float, float]:
        node = self._nodes[city_id]
        return node["lat"], node["lon"]

    def city_matches(self, name: str) -> list[int]:
        return [
            node_id
            for node_id, node in self._nodes.items()
            if node["name"].casefold() == name.casefold()
        ]

    def find_city(self, name: str, state: str | None = None) -> int:
        matches = [
            node_id
            for node_id in self.city_matches(name)
            if state is None or self.state(node_id).casefold() == state.casefold()
        ]
        if not matches:
            location = f" in state {state!r}" if state else ""
            raise ValueError(f"unknown city: {name!r}{location}")
        if len(matches) > 1:
            raise ValueError(f"city name is ambiguous: {name!r}; provide --state")
        return matches[0]
