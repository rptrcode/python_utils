"""
Filesystem Utilities

Contains functions and CLI handlers for file and directory manipulation,
such as recursively removing empty directories.
"""

import argparse
import os
import sys
from pathlib import Path


def delete_empty_directories(
    target_path: Path,
    dry_run: bool = False,
    delete_root: bool = False,
    verbose: bool = True,
) -> int:
    """Recursively removes empty directories within target_path.

    Args:
        target_path: Root directory path to start scanning from.
        dry_run: If True, only prints what would be deleted without deleting.
        delete_root: If True, allows deleting target_path itself if it is empty.
        verbose: If True, prints each deleted directory.

    Returns:
        The total number of empty directories deleted (or found in dry-run mode).
    """
    target_path = Path(target_path).resolve()

    if not target_path.exists():
        print(f"Error: Path does not exist: {target_path}", file=sys.stderr)
        return 0

    if not target_path.is_dir():
        print(f"Error: Path is not a directory: {target_path}", file=sys.stderr)
        return 0

    deleted_count = 0
    simulated_deleted: set[Path] = set()

    # topdown=False ensures we visit leaf directories before parent directories.
    for root, dirs, files in os.walk(target_path, topdown=False):
        current_dir = Path(root)

        # Skip the root directory itself unless explicitly requested
        if current_dir == target_path and not delete_root:
            continue

        try:
            # Check if directory is empty (or would become empty in dry-run mode)
            if dry_run:
                children = list(current_dir.iterdir())
                is_empty = not children or all(child in simulated_deleted for child in children)
            else:
                is_empty = not any(current_dir.iterdir())

            if is_empty:
                if dry_run:
                    simulated_deleted.add(current_dir)
                    if verbose:
                        print(f"[DRY RUN] Would delete: {current_dir}")
                else:
                    current_dir.rmdir()
                    if verbose:
                        print(f"Deleted: {current_dir}")
                deleted_count += 1
        except PermissionError:
            print(f"Permission denied: {current_dir}", file=sys.stderr)
        except OSError as e:
            print(f"Error removing {current_dir}: {e}", file=sys.stderr)

    return deleted_count


def run_clean_empty_dirs(args: argparse.Namespace) -> int:
    """CLI action handler for 'clean-empty-dirs' subcommand."""
    target_path = Path(args.path)
    action_label = "Would remove" if args.dry_run else "Removed"
    verbose = not args.quiet

    count = delete_empty_directories(
        target_path=target_path,
        dry_run=args.dry_run,
        delete_root=args.delete_root,
        verbose=verbose,
    )

    print(f"\n{action_label} {count} empty {'directory' if count == 1 else 'directories'}.")
    return 0


def register_subcommand(subparsers: argparse._SubParsersAction) -> None:
    """Registers filesystem-related subcommands to the main CLI parser."""
    parser = subparsers.add_parser(
        "clean-empty-dirs",
        aliases=["delete-empty-dirs"],
        help="Recursively delete empty directories in all subdirectories",
        description="Recursively scan and remove empty directories bottom-up.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Root directory to search (default: current directory)",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Simulate run without deleting anything",
    )
    parser.add_argument(
        "--delete-root",
        action="store_true",
        help="Also delete the target directory itself if it ends up empty",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress per-folder output; only print final summary",
    )
    parser.set_defaults(func=run_clean_empty_dirs)
