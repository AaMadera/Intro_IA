"""Classic Wumpus world physics, percepts, and scoring."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from wumpus.config import WorldConfig
from wumpus.types import Action, Direction, Percept, Position, neighbors4, step_from


@dataclass
class StepResult:
    percept: Percept
    reward: float
    done: bool
    info: dict[str, Any]


class WumpusWorld:
    """Partially observable grid cave. The agent only sees the five-tuple percept."""

    def __init__(self, config: WorldConfig) -> None:
        self.config = config
        self.reset()

    def reset(self) -> Percept:
        cfg = self.config
        self.pos = cfg.start
        self.direction = cfg.direction
        self.arrows = cfg.arrows
        self.has_gold = False
        self.gold_pos: Position | None = cfg.gold
        self.wumpus_pos = cfg.wumpus
        self.wumpus_alive = cfg.wumpus is not None
        self.dead = False
        self.climbed = False
        self.score = 0
        self.steps = 0
        self.done = False
        return self._sense(bump=False, scream=False)

    @property
    def pits(self) -> frozenset[Position]:
        return self.config.pits

    def in_bounds(self, pos: Position) -> bool:
        return self.config.in_bounds(pos) and pos not in self.config.walls

    def step(self, action: Action) -> StepResult:
        if self.done:
            percept = self._sense(bump=False, scream=False)
            return StepResult(percept, 0.0, True, self._info("already_done"))

        self.steps += 1
        reward = float(self.config.scoring.step)
        bump = False
        scream = False
        reason = "ok"

        if action is Action.TURN_LEFT:
            self.direction = self.direction.left()
        elif action is Action.TURN_RIGHT:
            self.direction = self.direction.right()
        elif action is Action.FORWARD:
            bump, reason = self._forward()
        elif action is Action.GRAB:
            if self.gold_pos is not None and self.pos == self.gold_pos:
                self.has_gold = True
                self.gold_pos = None
                reason = "grabbed_gold"
            else:
                reason = "grab_failed"
        elif action is Action.SHOOT:
            scream, reason, extra = self._shoot()
            reward += extra
        elif action is Action.CLIMB:
            if self.pos == self.config.start:
                self.climbed = True
                self.done = True
                if self.has_gold:
                    reward += float(self.config.scoring.gold)
                    reason = "climbed_with_gold"
                else:
                    reason = "climbed_empty"
            else:
                reason = "climb_failed_not_at_exit"

        if self.dead:
            reward += float(self.config.scoring.death)
            self.done = True
        if self.steps >= self.config.max_steps and not self.done:
            self.done = True
            reason = "max_steps"

        self.score += reward
        percept = self._sense(bump=bump, scream=scream)
        return StepResult(percept, reward, self.done, self._info(reason))

    def _forward(self) -> tuple[bool, str]:
        nxt = step_from(self.pos, self.direction)
        if not self.in_bounds(nxt):
            return True, "bump"
        self.pos = nxt
        if self.pos in self.config.pits:
            self.dead = True
            return False, "fell_in_pit"
        if self.wumpus_alive and self.pos == self.wumpus_pos:
            self.dead = True
            return False, "eaten_by_wumpus"
        return False, "moved"

    def _shoot(self) -> tuple[bool, str, float]:
        if self.arrows <= 0:
            return False, "no_arrows", 0.0
        self.arrows -= 1
        extra = float(self.config.scoring.shoot)
        if not self.wumpus_alive or self.wumpus_pos is None:
            return False, "shot_missed", extra
        if self._wumpus_in_line_of_fire():
            self.wumpus_alive = False
            return True, "wumpus_killed", extra
        return False, "shot_missed", extra

    def _wumpus_in_line_of_fire(self) -> bool:
        assert self.wumpus_pos is not None
        wx, wy = self.wumpus_pos
        x, y = self.pos
        dx, dy = self.direction.dx, self.direction.dy
        while True:
            x += dx
            y += dy
            cell = (x, y)
            if not self.in_bounds(cell):
                return False
            if cell == self.wumpus_pos:
                return True

    def _sense(self, bump: bool, scream: bool) -> Percept:
        adj = [n for n in neighbors4(self.pos) if self.config.in_bounds(n)]
        stench = bool(
            self.wumpus_alive
            and self.wumpus_pos is not None
            and self.wumpus_pos in adj
        )
        breeze = any(n in self.config.pits for n in adj)
        glitter = self.gold_pos is not None and self.pos == self.gold_pos
        return Percept(stench=stench, breeze=breeze, glitter=glitter, bump=bump, scream=scream)

    def _info(self, reason: str) -> dict[str, Any]:
        return {
            "reason": reason,
            "pos": self.pos,
            "direction": self.direction.name,
            "has_gold": self.has_gold,
            "dead": self.dead,
            "climbed": self.climbed,
            "score": self.score,
            "steps": self.steps,
            "arrows": self.arrows,
        }

    def render(self, percept: Percept | None = None) -> str:
        """God-view ASCII map. y increases upward, as in AIMA."""
        cfg = self.config
        lines = [
            f"Step {self.steps}  Score {self.score}  "
            f"{'DEAD' if self.dead else 'CLIMBED' if self.climbed else 'IN CAVE'}"
        ]
        for y in range(cfg.height, 0, -1):
            cells = []
            for x in range(1, cfg.width + 1):
                cells.append(self._cell_token((x, y)))
            lines.append(f"{y:2d} | " + " ".join(cells))
        x_axis = "     " + " ".join(f"{x:2d}" for x in range(1, cfg.width + 1))
        lines.append(x_axis)
        if percept is not None:
            lines.append(f"Percept {percept}")
        return "\n".join(lines)

    def _cell_token(self, pos: Position) -> str:
        if pos == self.pos and not self.climbed:
            return f"{self.direction.symbol()} "
        if pos in self.config.walls:
            return "##"
        marks = []
        if pos in self.config.pits:
            marks.append("P")
        if pos == self.wumpus_pos:
            marks.append("W" if self.wumpus_alive else "w")
        if pos == self.gold_pos:
            marks.append("G")
        if not marks:
            return ". "
        return ("".join(marks) + " ")[:2]
