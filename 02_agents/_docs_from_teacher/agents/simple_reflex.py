"""Simple reflex agent: condition-action rules on the current percept only."""

from __future__ import annotations

from agents.base import Agent
from wumpus.types import Action, Percept


class SimpleReflexAgent(Agent):
    """No memory. Dies often in the classic 4x4 cave — that is the point."""

    name = "simple-reflex"

    def act(self, percept: Percept) -> Action:
        if percept.glitter:
            return Action.GRAB
        if percept.bump:
            return Action.TURN_LEFT
        # Breeze or stench means the next square may be lethal.
        if percept.breeze or percept.stench:
            return Action.TURN_RIGHT
        return Action.FORWARD
