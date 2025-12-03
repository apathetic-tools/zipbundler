import argparse
import sys

from apathetic_logging import LEVEL_ORDER

from .actions import get_metadata
from .commands import handle_init_command, handle_list_command
from .logs import getAppLogger
from .meta import PROGRAM_DISPLAY


def _handle_early_exits(args: argparse.Namespace) -> int | None:
    """
    Handle early exit conditions (version, etc.).

    Returns exit code if we should exit early, None otherwise.
    """
    logger = getAppLogger()

    # --- Version flag ---
    if getattr(args, "version", None):
        meta = get_metadata()
        standalone = " [standalone]" if globals().get("__STANDALONE__", False) else ""
        logger.info(
            "%s %s (%s)%s", PROGRAM_DISPLAY, meta.version, meta.commit, standalone
        )
        return 0

    return None


def _setup_parser() -> argparse.ArgumentParser:
    """Define and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Bundle your packages into a runnable, importable zip"
    )

    # --- Version and verbosity (before subparsers) ---
    parser.add_argument("--version", action="store_true", help="Show version info.")

    subparsers = parser.add_subparsers(
        dest="command", help="Command to run", required=False
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

    # --- Handle early exits (version, etc.) ---
    early_exit_code = _handle_early_exits(parsed_args)
    if early_exit_code is not None:
        return early_exit_code

    # --- Handle subcommands ---
    if parsed_args.command == "init":
        return handle_init_command(parsed_args)
    if parsed_args.command == "list":
        return handle_list_command(parsed_args)

    # No command provided
    parser.error("No command specified. Use --help for usage.")
    return 1  # pragma: no cover


if __name__ == "__main__":
    sys.exit(main())
