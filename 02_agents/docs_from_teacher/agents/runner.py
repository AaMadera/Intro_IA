"""Run one episode of an agent in a Wumpus world."""

from __future__ import annotations

import time
from typing import Any

from agents.base import Agent
from wumpus.environment import WumpusWorld
from wumpus.types import Percept


def run_episode(
    world: WumpusWorld,
    agent: Agent,
    *,
    render: bool = True,
    delay: float = 0.0,
) -> dict[str, Any]:
    percept: Percept = world.reset()
    agent.reset()
    if render:
        print(world.render(percept))
        print(f"Agent: {agent.name}")
        print("-" * 40)

    while True:
        action = agent.act(percept)
        if render:
            print(f"Action: {action.value}")
        result = world.step(action)
        percept = result.percept
        if render:
            print(world.render(percept))
            print(f"Reward {result.reward:+.0f}  ({result.info['reason']})")
            print("-" * 40)
            if delay:
                time.sleep(delay)
        if result.done:
            break

    summary = {
        "score": world.score,
        "steps": world.steps,
        "dead": world.dead,
        "climbed": world.climbed,
        "has_gold": world.has_gold,
        "reason": result.info["reason"],
        "agent": agent.name,
    }
    print(_format_summary(summary))
    return summary


def _format_summary(summary: dict[str, Any]) -> str:
    outcome = "died" if summary["dead"] else "climbed" if summary["climbed"] else "stopped"
    gold = "with gold" if summary["has_gold"] else "without gold"
    return (
        f"Result: {outcome} {gold}  "
        f"steps={summary['steps']}  score={summary['score']}"
    )
