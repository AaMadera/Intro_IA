"""Shared CLI helpers for the six main programs."""

from __future__ import annotations

import argparse
from pathlib import Path

from wumpus.config import WorldConfig, load_config

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "config" / "classic_4x4.yaml"


def build_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="YAML world file (default: config/classic_4x4.yaml)",
    )
    parser.add_argument("--delay", type=float, default=0.0, help="Seconds to pause after each step")
    parser.add_argument("--quiet", action="store_true", help="Print only the episode summary")
    return parser


def load_world_config(args: argparse.Namespace) -> WorldConfig:
    return load_config(args.config)
