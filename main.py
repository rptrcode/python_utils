#!/usr/bin/env python3
"""
main.py - Generic Python Utilities CLI Suite

A centralized command-line interface for various utility tools.
New utility modules can easily be plugged in by adding them to COMMAND_MODULES.
"""

import argparse
import sys
from utils import fs_utils

# Register all utility modules here as you add more in the future.
# Each module should implement a `register_subcommand(subparsers)` function.
COMMAND_MODULES = [
    fs_utils,
]


def build_parser() -> argparse.ArgumentParser:
    """Constructs the root argument parser and populates all subcommands."""
    parser = argparse.ArgumentParser(
        prog="python3 main.py",
        description="Generic Python Utilities Suite - A collection of developer & system tools.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparsers = parser.add_subparsers(
        dest="command",
        title="Available Commands",
        metavar="<command>",
    )

    for module in COMMAND_MODULES:
        if hasattr(module, "register_subcommand"):
            module.register_subcommand(subparsers)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not args.command or not hasattr(args, "func"):
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
