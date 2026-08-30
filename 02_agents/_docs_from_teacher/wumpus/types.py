"""Shared types for the classic Wumpus world."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Tuple

# 1-based coordinates matching AIMA: (1, 1) is the bottom-left cave.
Position = Tuple[int, int]


class Direction(Enum):
    """Cardinal facing. Value is the (dx, dy) step of Forward."""

    NORTH = (0, 1)
    EAST = (1, 0)
    SOUTH = (0, -1)
    WEST = (-1, 0)

    @property
    def dx(self) -> int:
        return self.value[0]

    @property
    def dy(self) -> int:
        return self.value[1]

    def left(self) -> "Direction":
        order = (Direction.NORTH, Direction.WEST, Direction.SOUTH, Direction.EAST)
        return order[(order.index(self) + 1) % 4]

    def right(self) -> "Direction":
        order = (Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST)
        return order[(order.index(self) + 1) % 4]

    def symbol(self) -> str:
        return {
            Direction.NORTH: "^",
            Direction.EAST: ">",
            Direction.SOUTH: "v",
            Direction.WEST: "<",
        }[self]


DIRECTION_BY_NAME = {d.name.lower(): d for d in Direction}


class Action(Enum):
    FORWARD = "Forward"
    TURN_LEFT = "TurnLeft"
    TURN_RIGHT = "TurnRight"
    GRAB = "Grab"
    SHOOT = "Shoot"
    CLIMB = "Climb"


@dataclass(frozen=True)
class Percept:
    """Five-component percept from AIMA: [Stench, Breeze, Glitter, Bump, Scream]."""

    stench: bool = False
    breeze: bool = False
    glitter: bool = False
    bump: bool = False
    scream: bool = False

    def as_tuple(self) -> tuple[bool, bool, bool, bool, bool]:
        return (self.stench, self.breeze, self.glitter, self.bump, self.scream)

    def __str__(self) -> str:
        flags = []
        if self.stench:
            flags.append("Stench")
        if self.breeze:
            flags.append("Breeze")
        if self.glitter:
            flags.append("Glitter")
        if self.bump:
            flags.append("Bump")
        if self.scream:
            flags.append("Scream")
        return "[" + ", ".join(flags) + "]" if flags else "[None]"


def neighbors4(pos: Position) -> list[Position]:
    x, y = pos
    return [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]


def step_from(pos: Position, direction: Direction) -> Position:
    return (pos[0] + direction.dx, pos[1] + direction.dy)
