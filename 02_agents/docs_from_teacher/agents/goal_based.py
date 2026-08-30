"""Goal-based agent: search a path to the current goal on safe cells."""

from __future__ import annotations

from agents.base import Agent
from agents.planning import first_action_toward, is_aligned, turns_to_face
from agents.world_model import WorldModel
from wumpus.config import WorldConfig
from wumpus.types import Action, Direction, Percept, Position, step_from


class GoalBasedAgent(Agent):
    """Goals, in order: grab gold, return to (1,1), climb. Explore if gold is unknown."""

    name = "goal-based"

    def __init__(self, config: WorldConfig) -> None:
        self.config = config
        self.model = WorldModel(config)
        self._last_action: Action | None = None

    def reset(self) -> None:
        self.model.reset(self.config)
        self._last_action = None

    def act(self, percept: Percept) -> Action:
        self.model.integrate(percept, self._last_action)
        action = self._choose(percept)
        self._last_action = action
        return action

    def _choose(self, percept: Percept) -> Action:
        m = self.model
        if percept.glitter:
            return Action.GRAB
        if m.has_gold and m.pos == m.start:
            return Action.CLIMB

        walkable = m.safe_cells()
        goal = self._current_goal()
        if goal is not None:
            action = first_action_toward(m.pos, m.direction, goal, walkable)
            if action:
                return action

        shoot = self._shoot_if_blocking()
        if shoot:
            return shoot

        # Goal unreachable on safe cells: keep turning (do not walk into a possible pit).
        return Action.TURN_LEFT

    def _current_goal(self) -> Position | None:
        m = self.model
        if m.has_gold:
            return m.start
        if m.known_gold is not None:
            return m.known_gold
        unvisited = sorted(
            (c for c in m.safe_cells() if c not in m.visited),
            key=lambda c: abs(c[0] - m.pos[0]) + abs(c[1] - m.pos[1]),
        )
        return unvisited[0] if unvisited else None

    def _shoot_if_blocking(self) -> Action | None:
        """If the wumpus location is unique and we can face it safely, shoot."""
        m = self.model
        wumpus = m.known_wumpus()
        if wumpus is None or m.arrows <= 0 or not m.wumpus_alive:
            return None
        if is_aligned(m.pos, m.direction, wumpus) and self._clear_shot(m.pos, m.direction, wumpus):
            return Action.SHOOT
        for d in Direction:
            if is_aligned(m.pos, d, wumpus) and self._clear_shot(m.pos, d, wumpus):
                turns = turns_to_face(m.direction, d)
                return turns[0] if turns else Action.SHOOT
        return None

    def _clear_shot(self, pos: Position, direction: Direction, target: Position) -> bool:
        cursor = pos
        for _ in range(self.model.width + self.model.height):
            cursor = step_from(cursor, direction)
            if cursor == target:
                return True
            if not self.model.in_bounds(cursor):
                return False
        return False
