# src/zipbundler/commands/list.py

"""Handle the list subcommand."""

import argparse
import sys
from pathlib import Path
from typing import Any

from zipbundler.build import list_files
from zipbundler.logs import getAppLogger


def handle_list_command(args: argparse.Namespace) -> int:
    """Handle the list subcommand."""
    logger = getAppLogger()

    if not args.source:
        logger.error("source is required for list command")
        return 1

    try:
        packages = [Path(p) for p in args.source]
        files = list_files(packages, count=args.count)

        if args.count:
            # Count already printed by list_files
            result = 0
        elif args.tree:
            # Build a tree structure
            tree: dict[str, Any] = {}
            for _file_path, arcname in files:
                parts = arcname.parts
                current: dict[str, Any] = tree
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                # Add file
                if parts and parts[-1] not in current:
                    current[parts[-1]] = None

            def print_tree(
                node: dict[str, Any],
                prefix: str = "",
            ) -> None:
                """Print tree structure recursively."""
                items = sorted(node.items())
                for i, (name, children) in enumerate(items):
                    is_last_item = i == len(items) - 1
                    connector = "└── " if is_last_item else "├── "
                    sys.stdout.write(f"{prefix}{connector}{name}\n")
                    if children is not None:
                        extension = "    " if is_last_item else "│   "
                        print_tree(children, prefix + extension)

            print_tree(tree)
            result = 0
        else:
            # Simple list
            for _file_path, arcname in files:
                sys.stdout.write(f"{arcname}\n")
            result = 0
    except (ValueError, FileNotFoundError) as e:
        logger.errorIfNotDebug(str(e))
        result = 1
    except Exception as e:  # noqa: BLE001
        logger.criticalIfNotDebug("Unexpected error: %s", e)
        result = 1

    return result
