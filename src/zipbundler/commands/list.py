# src/zipbundler/commands/list.py

"""Handle the list subcommand."""

import argparse
from pathlib import Path
from typing import Any

from zipbundler.build import list_files, list_files_from_archive
from zipbundler.commands.zipapp_style import is_archive_file
from zipbundler.logs import getAppLogger


def handle_list_command(args: argparse.Namespace) -> int:
    """Handle the list subcommand."""
    logger = getAppLogger()

    if not args.include:
        logger.error("source is required for list command")
        return 1

    try:
        # Check if any source is an archive file
        sources = [Path(p) for p in args.include]
        is_archive = any(is_archive_file(src) for src in sources)

        if is_archive:
            # Handle archive files
            if len(sources) > 1:
                logger.error("Only one archive file can be listed at a time")
                return 1

            archive_path = sources[0]
            if not is_archive_file(archive_path):
                logger.error("Source must be an archive file (.pyz) or directory")
                return 1

            # Always get files (not count-only) so we can build tree
            files = list_files_from_archive(archive_path, count=False)
        else:
            # Handle directory sources (existing behavior)
            packages = sources
            # Always get files (not count-only) so we can build tree
            files = list_files(packages, count=False)

        # Always show count at brief level
        file_count = len(files)
        logger.brief("Files: %d", file_count)

        # Always build and show tree at detail level
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
                logger.detail(f"{prefix}{connector}{name}")
                if children is not None:
                    extension = "    " if is_last_item else "│   "
                    print_tree(children, prefix + extension)

        print_tree(tree)
        result = 0
    except (ValueError, FileNotFoundError) as e:
        logger.errorIfNotDebug(str(e))
        result = 1
    except Exception as e:  # noqa: BLE001
        logger.criticalIfNotDebug("Unexpected error: %s", e)
        result = 1

    return result
