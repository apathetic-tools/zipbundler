import argparse
import sys
from pathlib import Path
from typing import Any

from apathetic_logging import LEVEL_ORDER

from .build import list_files
from .logs import getAppLogger


def _get_default_config_content() -> str:
    """Generate default .zipbundler.jsonc config file content."""
    return """{
  // Packages to include (glob patterns or package names)
  "packages": [
    "src/my_package/**/*.py"
  ],

  // Files/directories to exclude (glob patterns)
  "exclude": [
    "**/__pycache__/**",
    "**/*.pyc",
    "**/*.pyo",
    "**/tests/**",
    "**/.git/**"
  ],

  // Output configuration
  "output": {
    "path": "dist/my_package.zip"
  },

  // Entry point for executable zip (optional)
  // "entry_point": "my_package.__main__:main",

  // Control code generation
  "options": {
    "shebang": "/usr/bin/env python3",
    "main_guard": true,
    "compression": "deflate"
  },

  // Metadata (optional)
  // "metadata": {
  //   "display_name": "My Package",
  //   "description": "Package description",
  //   "version": "1.0.0"
  // }
}
"""


def _handle_init_command(args: argparse.Namespace) -> int:
    """Handle the init subcommand."""
    logger = getAppLogger()

    config_path = Path(args.output or ".zipbundler.jsonc")

    if config_path.exists() and not args.force:
        logger.error(
            "Configuration file already exists: %s\nUse --force to overwrite.",
            config_path,
        )
        return 1

    try:
        config_content = _get_default_config_content()
        config_path.write_text(config_content, encoding="utf-8")
        logger.info("Created configuration file: %s", config_path)
    except OSError:
        logger.exception("Failed to create configuration file")
        return 1
    except Exception as e:  # noqa: BLE001
        logger.criticalIfNotDebug("Unexpected error: %s", e)
        return 1
    else:
        return 0


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


def _setup_parser() -> argparse.ArgumentParser:
    """Define and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Bundle your packages into a runnable, importable zip"
    )
    subparsers = parser.add_subparsers(
        dest="command", help="Command to run", required=True
    )

    # Init command
    init_parser = subparsers.add_parser(
        "init",
        help="Create a default .zipbundler.jsonc config file",
    )
    init_parser.add_argument(
        "-o",
        "--output",
        help="Output path for config file (default: .zipbundler.jsonc)",
    )
    init_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing config file",
    )

    # Add log level options to init parser
    log_level_init = init_parser.add_mutually_exclusive_group()
    log_level_init.add_argument(
        "-q",
        "--quiet",
        action="store_const",
        const="warning",
        dest="log_level",
        help="Suppress non-critical output (same as --log-level warning).",
    )
    log_level_init.add_argument(
        "-v",
        "--verbose",
        action="store_const",
        const="debug",
        dest="log_level",
        help="Verbose output (same as --log-level debug).",
    )
    log_level_init.add_argument(
        "--log-level",
        choices=LEVEL_ORDER,
        default=None,
        dest="log_level",
        help="Set log verbosity level.",
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

    return parser


def main(args: list[str] | None = None) -> int:
    """Main entry point for the zipbundler CLI."""
    logger = getAppLogger()

    parser = _setup_parser()
    parsed_args = parser.parse_args(args)

    # Initialize logger with CLI args
    resolved_log_level = logger.determineLogLevel(args=parsed_args)
    logger.setLevel(resolved_log_level)

    if parsed_args.command == "init":
        return _handle_init_command(parsed_args)
    if parsed_args.command == "list":
        return _handle_list_command(parsed_args)

    # This should never be reached due to required=True on subparsers
    parser.error("Unknown command")  # pragma: no cover
    return 1  # pragma: no cover


if __name__ == "__main__":
    sys.exit(main())
