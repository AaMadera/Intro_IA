"""Agent program interface (architecture + program, AIMA ch. 2)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from wumpus.types import Action, Percept


class Agent(ABC):
    """Maps a percept to an action. Subclasses may keep internal state."""

    name = "agent"

    def reset(self) -> None:
        """Called at the start of each episode."""

    @abstractmethod
    def act(self, percept: Percept) -> Action:
        raise NotImplementedError
