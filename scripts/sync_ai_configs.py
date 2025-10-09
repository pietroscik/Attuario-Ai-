#!/usr/bin/env python3
"""
Sync AI config files from this repo into another repo's .github/ai_config directory.

Usage:
    python scripts/sync_ai_configs.py --dest /path/to/attuario-eu
"""

import argparse
import shutil
from pathlib import Path
import sys


def sync_configs(src: Path, dest_root: Path) -> None:
    if not src.is_dir():
        raise FileNotFoundError(f"Source directory not found: {src}")

    dest = dest_root / ".github" / "ai_config"
    dest.mkdir(parents=True, exist_ok=True)

    for item in src.iterdir():
        if item.is_file():
            shutil.copy2(item, dest / item.name)
        # se servono anche sottocartelle, sostituire con shutil.copytree con dirs_exist_ok=True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sync AI config files to a target repository."
    )
    parser.add_argument(
        "--src",
        default=".github/ai_config",
        help="Source directory with AI config files (default: .github/ai_config)",
    )
    parser.add_argument(
        "--dest",
        required=True,
        help="Destination repository root path (the .github/ai_config folder will be created ins)",
    )
    args = parser.parse_args()

    try:
        sync_configs(Path(args.src), Path(args.dest))
    except Exception as exc:  # noqa: BLE001 (semplice CLI)
        print(f"[sync-ai-configs] ERROR: {exc}", file=sys.stderr)
        return 1

    print("[sync-ai-configs] Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
