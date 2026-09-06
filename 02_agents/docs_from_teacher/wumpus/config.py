"""Load and validate a classic Wumpus world from YAML."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from wumpus.types import DIRECTION_BY_NAME, Direction, Position


@dataclass(frozen=True)
class Scoring:
    gold: int = 1000
    death: int = -1000
    step: int = -1
    shoot: int = -10


@dataclass(frozen=True)
class WorldConfig:
    width: int
    height: int
    start: Position
    direction: Direction
    arrows: int
    wumpus: Position | None
    pits: frozenset[Position]
    gold: Position
    walls: frozenset[Position]
    scoring: Scoring = field(default_factory=Scoring)
    seed: int | None = None
    max_steps: int = 200
    source: Path | None = None

    def in_bounds(self, pos: Position) -> bool:
        x, y = pos
        return 1 <= x <= self.width and 1 <= y <= self.height


def load_config(path: str | Path) -> WorldConfig:
    path = Path(path)
    with path.open(encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    return parse_config(raw, source=path)


def parse_config(raw: dict[str, Any], source: Path | None = None) -> WorldConfig:
    grid = raw.get("grid") or {}
    width = int(grid.get("width", 4))
    height = int(grid.get("height", 4))
    if width < 2 or height < 2:
        raise ValueError("grid width and height must be at least 2")

    agent = raw.get("agent") or {}
    start = _as_position(agent.get("start", [1, 1]), "agent.start")
    direction = DIRECTION_BY_NAME.get(str(agent.get("direction", "east")).lower())
    if direction is None:
        raise ValueError("agent.direction must be north, east, south, or west")
    arrows = int(agent.get("arrows", 1))
    if arrows < 0:
        raise ValueError("agent.arrows must be >= 0")

    wumpus_raw = raw.get("wumpus")
    wumpus = None if wumpus_raw in (None, [], "none") else _as_position(wumpus_raw, "wumpus")

    pits = frozenset(_as_position(p, "pits") for p in (raw.get("pits") or []))
    gold = _as_position(raw.get("gold", [2, 2]), "gold")
    walls = frozenset(_as_position(w, "walls") for w in (raw.get("walls") or []))

    scoring_raw = raw.get("scoring") or {}
    scoring = Scoring(
        gold=int(scoring_raw.get("gold", 1000)),
        death=int(scoring_raw.get("death", -1000)),
        step=int(scoring_raw.get("step", -1)),
        shoot=int(scoring_raw.get("shoot", -10)),
    )

    seed = raw.get("seed")
    max_steps = int(raw.get("max_steps", 200))
    if max_steps < 1:
        raise ValueError("max_steps must be >= 1")

    cfg = WorldConfig(
        width=width,
        height=height,
        start=start,
        direction=direction,
        arrows=arrows,
        wumpus=wumpus,
        pits=pits,
        gold=gold,
        walls=walls,
        scoring=scoring,
        seed=None if seed is None else int(seed),
        max_steps=max_steps,
        source=source,
    )
    _validate(cfg)
    return cfg


def _as_position(value: Any, label: str) -> Position:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError(f"{label} must be a [x, y] pair (1-based)")
    return (int(value[0]), int(value[1]))


def _validate(cfg: WorldConfig) -> None:
    labeled = {
        "agent.start": cfg.start,
        "gold": cfg.gold,
    }
    if cfg.wumpus is not None:
        labeled["wumpus"] = cfg.wumpus
    for name, pos in labeled.items():
        if not cfg.in_bounds(pos):
            raise ValueError(f"{name} {pos} is outside the {cfg.width}x{cfg.height} grid")
        if pos in cfg.walls:
            raise ValueError(f"{name} {pos} overlaps a wall")

    for pos in cfg.pits:
        if not cfg.in_bounds(pos):
            raise ValueError(f"pit {pos} is outside the grid")
        if pos in cfg.walls:
            raise ValueError(f"pit {pos} overlaps a wall")
    for pos in cfg.walls:
        if not cfg.in_bounds(pos):
            raise ValueError(f"wall {pos} is outside the grid")

    if cfg.start in cfg.pits:
        raise ValueError("the agent cannot start on a pit")
    if cfg.wumpus is not None and cfg.start == cfg.wumpus:
        raise ValueError("the agent cannot start on the wumpus")
    if cfg.gold in cfg.pits:
        raise ValueError("gold cannot be placed on a pit")
    if cfg.wumpus is not None and cfg.gold == cfg.wumpus:
        raise ValueError("gold cannot be placed on the wumpus")
    if cfg.wumpus is not None and cfg.wumpus in cfg.pits:
        raise ValueError("the wumpus cannot sit on a pit")
