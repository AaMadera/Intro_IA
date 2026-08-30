#!/usr/bin/env python3
"""Program 3: model-based agent in the Wumpus world."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from agents.cli import build_parser, load_world_config  # noqa: E402
from agents.model_based import ModelBasedAgent  # noqa: E402
from agents.runner import run_episode  # noqa: E402
from wumpus.environment import WumpusWorld  # noqa: E402


def main() -> None:
    parser = build_parser("Model-based agent (safe-cell map) in the Wumpus world.")
    args = parser.parse_args()
    config = load_world_config(args)
    world = WumpusWorld(config)
    agent = ModelBasedAgent(config)
    run_episode(world, agent, render=not args.quiet, delay=args.delay)


if __name__ == "__main__":
    main()
