#!/usr/bin/env python3
"""Program 1: classic Wumpus world (environment only)."""

from __future__ import annotations

import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from agents.cli import DEFAULT_CONFIG  # noqa: E402
from wumpus.config import load_config  # noqa: E402
from wumpus.environment import WumpusWorld  # noqa: E402
from wumpus.types import Action  # noqa: E402

KEY_TO_ACTION = {
    "f": Action.FORWARD,
    "l": Action.TURN_LEFT,
    "r": Action.TURN_RIGHT,
    "g": Action.GRAB,
    "s": Action.SHOOT,
    "c": Action.CLIMB,
}


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run the classic Wumpus world.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--mode",
        choices=("show", "random", "keyboard"),
        default="show",
        help="show = print the cave and exit; random = random actions; keyboard = play",
    )
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    config = load_config(args.config)
    world = WumpusWorld(config)
    percept = world.reset()
    print(world.render(percept))
    print()
    print("Legend: >^v< agent  P pit  W wumpus  w dead wumpus  G gold  . empty  ## wall")

    if args.mode == "show":
        print(f"\nLoaded {args.config}  ({config.width}x{config.height})")
        return

    if args.mode == "random":
        rng = random.Random(args.seed)
        actions = list(Action)
        while not world.done:
            action = rng.choice(actions)
            print(f"\nAction: {action.value}")
            result = world.step(action)
            print(world.render(result.percept))
            print(f"Reward {result.reward:+.0f}  ({result.info['reason']})")
        _print_end(world)
        return

    print("\nKeys: f=Forward  l=TurnLeft  r=TurnRight  g=Grab  s=Shoot  c=Climb  q=Quit")
    while not world.done:
        raw = input("action> ").strip().lower()
        if raw in {"q", "quit"}:
            break
        action = KEY_TO_ACTION.get(raw)
        if action is None:
            print("Unknown key. Use f l r g s c q.")
            continue
        result = world.step(action)
        print(world.render(result.percept))
        print(f"Reward {result.reward:+.0f}  ({result.info['reason']})")
    _print_end(world)


def _print_end(world: WumpusWorld) -> None:
    outcome = "died" if world.dead else "climbed" if world.climbed else "stopped"
    gold = "with gold" if world.has_gold else "without gold"
    print(f"\nResult: {outcome} {gold}  steps={world.steps}  score={world.score}")


if __name__ == "__main__":
    main()
