"""Model-based reflex agent: act from an inferred map of safe caves."""

from __future__ import annotations

from agents.base import Agent
from agents.planning import first_action_toward
from agents.world_model import WorldModel
from wumpus.config import WorldConfig
from wumpus.types import Action, Percept


class ModelBasedAgent(Agent):
    """Keeps pose + breeze/stench history. Never steps into an unsafe cave."""

    name = "model-based"

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
        if m.has_gold:
            action = first_action_toward(m.pos, m.direction, m.start, walkable)
            return action or Action.TURN_LEFT

        if m.known_gold is not None and m.is_safe(m.known_gold):
            action = first_action_toward(m.pos, m.direction, m.known_gold, walkable)
            if action:
                return action

        unvisited_safe = [c for c in walkable if c not in m.visited]
        unvisited_safe.sort(key=lambda c: abs(c[0] - m.pos[0]) + abs(c[1] - m.pos[1]))
        for dest in unvisited_safe:
            action = first_action_toward(m.pos, m.direction, dest, walkable)
            if action:
                return action

        # Nothing left that is known-safe: turn in place rather than gamble.
        return Action.TURN_LEFT
