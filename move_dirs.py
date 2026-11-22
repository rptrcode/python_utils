#!/usr/bin/env python3
"""Move all .mp3 files inside a target directory one directory level up."""

import argparse
from pathlib import Path
import shutil
import sys


def move_mp3s_up(root_dir: Path, dry_run: bool = False) -> None:
    if not root_dir.exists() or not root_dir.is_dir():
        print(f"Error: '{root_dir}' is not a valid directory.", file=sys.stderr)
        sys.exit(1)

    root_resolved = root_dir.resolve()
    moved_count = 0
    skipped_count = 0

    for mp3_path in root_resolved.rglob("*"):
        if not mp3_path.is_file() or mp3_path.suffix.lower() != ".mp3":
            continue

        # Skip files already directly inside the root directory
        if mp3_path.parent == root_resolved:
            continue

        dest_dir = mp3_path.parent.parent
        dest_path = dest_dir / mp3_path.name

        if dest_path.exists():
            print(f"[SKIP - exists] {mp3_path} -> {dest_path}")
            skipped_count += 1
            continue

        if dry_run:
            print(f"[DRY RUN] {mp3_path} -> {dest_path}")
        else:
            shutil.move(str(mp3_path), str(dest_path))
            print(f"[MOVED]   {mp3_path} -> {dest_path}")
        moved_count += 1

    print(f"\nSummary: {moved_count} moved, {skipped_count} skipped.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Move all .mp3 files found inside a directory one level up."
    )
    parser.add_argument(
        "directory",
        type=Path,
        help="Target directory to scan for .mp3 files",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview moves without modifying any files",
    )
    args = parser.parse_args()
    move_mp3s_up(args.directory, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
