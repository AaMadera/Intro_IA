#!/usr/bin/env python3
"""Program 6: learning agent (Q-learning) in the Wumpus world."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from agents.cli import build_parser, load_world_config  # noqa: E402
from agents.learning import LearningAgent, train  # noqa: E402
from agents.runner import run_episode  # noqa: E402
from wumpus.environment import WumpusWorld  # noqa: E402


def main() -> None:
    parser = build_parser("Learning agent trained with Q-learning on one Wumpus cave.")
    parser.add_argument("--episodes", type=int, default=1500, help="Training episodes")
    parser.add_argument("--epsilon", type=float, default=0.25)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--skip-demo", action="store_true", help="Do not render a greedy episode")
    args = parser.parse_args()

    config = load_world_config(args)
    world = WumpusWorld(config)
    agent = LearningAgent(config, epsilon=args.epsilon, seed=args.seed)

    scores = train(world, agent, args.episodes)
    last = scores[-50:] if len(scores) >= 50 else scores
    print(f"Trained {args.episodes} episodes on {args.config}")
    print(f"Mean score (all): {sum(scores) / len(scores):.1f}")
    print(f"Mean score (last {len(last)}): {sum(last) / len(last):.1f}")
    print(f"Q-table size: {len(agent.q)} state-action pairs")

    if args.skip_demo:
        return

    print("\n--- Greedy demo (epsilon = 0) ---\n")
    agent.training = False
    agent.epsilon = 0.0
    run_episode(world, agent, render=not args.quiet, delay=args.delay)


if __name__ == "__main__":
    main()
