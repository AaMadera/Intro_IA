"""Utility-based agent: choose the action that starts the highest-value plan."""

from __future__ import annotations

from dataclasses import dataclass

from agents.base import Agent
from agents.planning import path_to_actions, shortest_path, turns_to_face
from agents.world_model import WorldModel
from wumpus.config import WorldConfig
from wumpus.types import Action, Direction, Percept, Position, step_from


@dataclass(frozen=True)
class Plan:
    actions: tuple[Action, ...]
    utility: float
    label: str


class UtilityBasedAgent(Agent):
    """Trades off gold, death risk, step cost, and the cost of the arrow."""

    name = "utility-based"
    STEP_COST = 1.0
    DEATH_COST = 1000.0
    GOLD_VALUE = 1000.0
    SHOOT_COST = 10.0
    EXPLORE_VALUE = 25.0

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

        plans = self._candidate_plans()
        if not plans:
            return Action.TURN_LEFT
        best = max(plans, key=lambda p: p.utility)
        return best.actions[0] if best.actions else Action.TURN_LEFT

    def _candidate_plans(self) -> list[Plan]:
        m = self.model
        safe = m.safe_cells()
        plans: list[Plan] = []

        if m.has_gold:
            plans.extend(self._plans_to(m.start, safe, self.GOLD_VALUE, "return-home"))
        elif m.known_gold is not None:
            gold_plans = self._plans_to(m.known_gold, safe, self.GOLD_VALUE, "go-to-gold")
            plans.extend(gold_plans)
            # Also consider going home empty if gold looks too risky (no safe path).
            if not gold_plans:
                plans.extend(self._plans_to(m.start, safe, 0.0, "abort-home"))

        for cell in safe:
            if cell not in m.visited:
                plans.extend(
                    self._plans_to(cell, safe, self.EXPLORE_VALUE, f"explore-{cell}")
                )

        # One-step risky probes: maybe the gold sits behind an unknown square.
        if not m.has_gold and m.known_gold is None:
            plans.extend(self._risky_step_plans(safe))

        plans.extend(self._shoot_plans())
        return [p for p in plans if p.actions]

    def _plans_to(
        self,
        dest: Position,
        walkable: set[Position],
        prize: float,
        label: str,
        extra_risk: float = 0.0,
    ) -> list[Plan]:
        m = self.model
        path = shortest_path(m.pos, dest, walkable)
        if path is None:
            return []
        actions = path_to_actions(m.direction, path)
        if dest == m.start and m.has_gold:
            actions = list(actions) + [Action.CLIMB]
        if dest == m.known_gold and not m.has_gold:
            actions = list(actions) + [Action.GRAB]
        if not actions:
            return []
        utility = prize - self.STEP_COST * len(actions) - self.DEATH_COST * extra_risk
        return [Plan(tuple(actions), utility, label)]

    def _risky_step_plans(self, safe: set[Position]) -> list[Plan]:
        m = self.model
        plans = []
        frontier = []
        for cell in safe:
            for n in m.neighbors(cell):
                if n not in safe and n not in m.visited:
                    frontier.append(n)
        seen: set[Position] = set()
        for cell in frontier:
            if cell in seen:
                continue
            seen.add(cell)
            p_death = m.pit_probability(cell)
            if m.wumpus_alive and not m.cannot_be_wumpus(cell):
                p_death = min(0.95, p_death + 0.25)
            walkable = set(safe) | {cell}
            plans.extend(
                self._plans_to(
                    cell,
                    walkable,
                    self.EXPLORE_VALUE * (1.0 - p_death),
                    f"risk-{cell}",
                    extra_risk=p_death,
                )
            )
        return plans

    def _shoot_plans(self) -> list[Plan]:
        m = self.model
        wumpus = m.known_wumpus()
        if wumpus is None or m.arrows <= 0 or not m.wumpus_alive:
            return []
        # Standing still and turning onto the line of fire, then shooting.
        for d in Direction:
            if not self._aims_at(m.pos, d, wumpus):
                continue
            turns = turns_to_face(m.direction, d)
            actions = list(turns) + [Action.SHOOT]
            utility = 80.0 - self.SHOOT_COST - self.STEP_COST * len(actions)
            return [Plan(tuple(actions), utility, "shoot-wumpus")]
        return []

    def _aims_at(self, pos: Position, direction: Direction, target: Position) -> bool:
        cursor = pos
        for _ in range(self.model.width + self.model.height):
            cursor = step_from(cursor, direction)
            if cursor == target:
                return True
            if not self.model.in_bounds(cursor):
                return False
        return False
