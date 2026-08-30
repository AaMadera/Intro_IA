"""Internal world model: pose tracking plus pit/wumpus safety inference."""

from __future__ import annotations

from wumpus.config import WorldConfig
from wumpus.types import Action, Direction, Percept, Position, neighbors4, step_from


class WorldModel:
    """What a model-based agent believes about the cave.

    The environment never tells the agent its coordinates. Pose is updated
    from the agent's own actions and the Bump percept.
    """

    def __init__(self, config: WorldConfig) -> None:
        self.width = config.width
        self.height = config.height
        self.start = config.start
        self.walls = set(config.walls)
        self.reset(config)

    def reset(self, config: WorldConfig | None = None) -> None:
        if config is not None:
            self.arrows = config.arrows
        self.pos = self.start
        self.direction = Direction.EAST if config is None else config.direction
        self.visited: set[Position] = {self.start}
        self.breeze: dict[Position, bool] = {}
        self.stench: dict[Position, bool] = {}
        self.known_gold: Position | None = None
        self.has_gold = False
        self.wumpus_alive = True
        self.prev_glitter = False
        self.last_action: Action | None = None

    def in_bounds(self, pos: Position) -> bool:
        x, y = pos
        return 1 <= x <= self.width and 1 <= y <= self.height and pos not in self.walls

    def neighbors(self, pos: Position) -> list[Position]:
        return [n for n in neighbors4(pos) if self.in_bounds(n)]

    def integrate(self, percept: Percept, last_action: Action | None) -> None:
        if last_action is Action.FORWARD and not percept.bump:
            nxt = step_from(self.pos, self.direction)
            if self.in_bounds(nxt):
                self.pos = nxt
        elif last_action is Action.TURN_LEFT:
            self.direction = self.direction.left()
        elif last_action is Action.TURN_RIGHT:
            self.direction = self.direction.right()
        elif last_action is Action.GRAB and self.prev_glitter:
            self.has_gold = True
            self.known_gold = None
        elif last_action is Action.SHOOT:
            self.arrows = max(0, self.arrows - 1)
            if percept.scream:
                self.wumpus_alive = False

        self.visited.add(self.pos)
        self.breeze[self.pos] = percept.breeze
        self.stench[self.pos] = percept.stench
        if percept.glitter:
            self.known_gold = self.pos
        if percept.scream:
            self.wumpus_alive = False
        self.prev_glitter = percept.glitter
        self.last_action = last_action

    def cannot_be_pit(self, cell: Position) -> bool:
        if cell == self.start or cell in self.visited:
            return True
        return any(self.breeze.get(n) is False for n in self.neighbors(cell))

    def cannot_be_wumpus(self, cell: Position) -> bool:
        if not self.wumpus_alive or cell == self.start or cell in self.visited:
            return True
        known = self.known_wumpus()
        if known is not None and cell != known:
            return True
        return any(self.stench.get(n) is False for n in self.neighbors(cell))

    def is_safe(self, cell: Position) -> bool:
        return self.in_bounds(cell) and self.cannot_be_pit(cell) and self.cannot_be_wumpus(cell)

    def safe_cells(self) -> set[Position]:
        cells = {
            (x, y)
            for x in range(1, self.width + 1)
            for y in range(1, self.height + 1)
            if self.is_safe((x, y))
        }
        return cells

    def known_wumpus(self) -> Position | None:
        """If exactly one cave can still hold a live wumpus, return it."""
        if not self.wumpus_alive:
            return None
        candidates: set[Position] = set()
        stench_cells = [c for c, has in self.stench.items() if has]
        if not stench_cells:
            return None
        for cell in stench_cells:
            for n in self.neighbors(cell):
                if n not in self.visited and not any(
                    self.stench.get(m) is False for m in self.neighbors(n)
                ):
                    candidates.add(n)
        if len(candidates) == 1:
            return next(iter(candidates))
        return None

    def pit_probability(self, cell: Position) -> float:
        """Crude probability used by the utility-based agent."""
        if not self.in_bounds(cell) or self.cannot_be_pit(cell):
            return 0.0
        if cell in self.visited:
            return 0.0
        # A breeze with few unexplained neighbors makes a pit more likely.
        breeze_neighbors = [n for n in self.neighbors(cell) if self.breeze.get(n) is True]
        if not breeze_neighbors:
            return 0.2
        unexplained = []
        for b in breeze_neighbors:
            unknown = [
                n
                for n in self.neighbors(b)
                if n not in self.visited and not self.cannot_be_pit(n)
            ]
            unexplained.append(len(unknown) or 1)
        return min(0.9, max(0.2, 1.0 / min(unexplained)))
