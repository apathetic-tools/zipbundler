import argparse
import sys
from pathlib import Path
from typing import Any

from apathetic_logging import LEVEL_ORDER

from .build import list_files
from .logs import getAppLogger


def _handle_list_command(args: argparse.Namespace) -> int:
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


def main(args: list[str] | None = None) -> int:
    """Main entry point for the zipbundler CLI."""
    logger = getAppLogger()

    parser = argparse.ArgumentParser(
        description="Bundle your packages into a runnable, importable zip"
    )
    subparsers = parser.add_subparsers(
        dest="command", help="Command to run", required=True
    )

    # List command
    list_parser = subparsers.add_parser(
        "list",
        help="List packages and files that would be included in the bundle",
    )
    list_parser.add_argument(
        "source",
        nargs="+",
        help="Source package directories to list",
    )
    list_parser.add_argument(
        "--tree",
        action="store_true",
        help="Show as directory tree",
    )
    list_parser.add_argument(
        "--count",
        action="store_true",
        help="Show file count only",
    )

    # Add log level options to list parser
    log_level_list = list_parser.add_mutually_exclusive_group()
    log_level_list.add_argument(
        "-q",
        "--quiet",
        action="store_const",
        const="warning",
        dest="log_level",
        help="Suppress non-critical output (same as --log-level warning).",
    )
    log_level_list.add_argument(
        "-v",
        "--verbose",
        action="store_const",
        const="debug",
        dest="log_level",
        help="Verbose output (same as --log-level debug).",
    )
    log_level_list.add_argument(
        "--log-level",
        choices=LEVEL_ORDER,
        default=None,
        dest="log_level",
        help="Set log verbosity level.",
    )

    parsed_args = parser.parse_args(args)

    # Initialize logger with CLI args
    resolved_log_level = logger.determineLogLevel(args=parsed_args)
    logger.setLevel(resolved_log_level)

    if parsed_args.command == "list":
        return _handle_list_command(parsed_args)

    # This should never be reached due to required=True on subparsers
    parser.error("Unknown command")  # pragma: no cover
    return 1  # pragma: no cover


if __name__ == "__main__":
    sys.exit(main())
