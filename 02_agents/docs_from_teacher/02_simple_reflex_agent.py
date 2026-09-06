#!/usr/bin/env python3
"""Program 2: simple reflex agent in the Wumpus world."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from agents.cli import build_parser, load_world_config  # noqa: E402
from agents.runner import run_episode  # noqa: E402
from agents.simple_reflex import SimpleReflexAgent  # noqa: E402
from wumpus.environment import WumpusWorld  # noqa: E402


def main() -> None:
    parser = build_parser("Simple reflex agent (no memory) in the Wumpus world.")
    args = parser.parse_args()
    config = load_world_config(args)
    world = WumpusWorld(config)
    agent = SimpleReflexAgent()
    run_episode(world, agent, render=not args.quiet, delay=args.delay)


if __name__ == "__main__":
    main()
