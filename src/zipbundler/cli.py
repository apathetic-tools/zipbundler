import argparse
import sys

from apathetic_logging import LEVEL_ORDER
from apathetic_utils import detect_runtime_mode

from .actions import get_metadata
from .commands import (
    handle_build_command,
    handle_info_command,
    handle_init_command,
    handle_list_command,
    handle_validate_command,
    handle_watch_command,
)
from .logs import getAppLogger
from .meta import PROGRAM_DISPLAY, PROGRAM_PACKAGE


def _handle_early_exits(args: argparse.Namespace) -> int | None:
    """
    Handle early exit conditions (version, etc.).

    Returns exit code if we should exit early, None otherwise.
    """
    logger = getAppLogger()

    # --- Version flag ---
    if getattr(args, "version", None):
        meta = get_metadata()
        runtime_mode = detect_runtime_mode(PROGRAM_PACKAGE)
        standalone = " [standalone]" if runtime_mode == "standalone" else ""
        logger.info(
            "%s %s (%s)%s", PROGRAM_DISPLAY, meta.version, meta.commit, standalone
        )
        return 0

    return None


def _setup_parser() -> argparse.ArgumentParser:  # noqa: PLR0915
    """Define and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Bundle your packages into a runnable, importable zip"
    )

    # --- Version and verbosity (before subparsers) ---
    parser.add_argument("--version", action="store_true", help="Show version info.")

    # --- zipapp-style --info flag ---
    parser.add_argument(
        "--info",
        action="store_true",
        help="Display the interpreter from an existing archive",
    )

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

    # Build command
    build_parser = subparsers.add_parser(
        "build",
        help="Build zip from current directory or config",
    )
    build_parser.add_argument(
        "-c",
        "--config",
        help=(
            "Path to configuration file (default: .zipbundler.jsonc or pyproject.toml)"
        ),
    )
    build_parser.add_argument(
        "-o",
        "--output",
        help="Output file path (overrides config)",
    )
    build_parser.add_argument(
        "-m",
        "--main",
        dest="entry_point",
        help="Entry point (module:function or module, overrides config)",
    )
    build_parser.add_argument(
        "-p",
        "--python",
        dest="shebang",
        help="Shebang line (overrides config)",
    )
    build_parser.add_argument(
        "--compress",
        action="store_true",
        help="Compress the zip file (overrides config)",
    )
    build_parser.add_argument(
        "--no-compress",
        action="store_false",
        dest="compress",
        help="Do not compress the zip file (overrides config)",
    )
    build_parser.add_argument(
        "--exclude",
        nargs="+",
        help="Exclude patterns (overrides config)",
    )
    build_parser.add_argument(
        "--main-guard",
        action="store_true",
        default=None,
        dest="main_guard",
        help=(
            "Wrap entry point in 'if __name__ == \"__main__\":' guard "
            "(overrides config)"
        ),
    )
    build_parser.add_argument(
        "--no-main-guard",
        action="store_false",
        dest="main_guard",
        help="Do not wrap entry point in main guard (overrides config)",
    )
    build_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be bundled without creating zip",
    )
    build_parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on config validation warnings",
    )

    # Add log level options to build parser
    log_level_build = build_parser.add_mutually_exclusive_group()
    log_level_build.add_argument(
        "-q",
        "--quiet",
        action="store_const",
        const="warning",
        dest="log_level",
        help="Suppress non-critical output (same as --log-level warning).",
    )
    log_level_build.add_argument(
        "-v",
        "--verbose",
        action="store_const",
        const="debug",
        dest="log_level",
        help="Verbose output (same as --log-level debug).",
    )
    log_level_build.add_argument(
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

    # Validate command
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate configuration file",
    )
    validate_parser.add_argument(
        "-c",
        "--config",
        help=(
            "Path to configuration file (default: .zipbundler.jsonc or pyproject.toml)"
        ),
    )
    validate_parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on warnings",
    )

    # Add log level options to validate parser
    log_level_validate = validate_parser.add_mutually_exclusive_group()
    log_level_validate.add_argument(
        "-q",
        "--quiet",
        action="store_const",
        const="warning",
        dest="log_level",
        help="Suppress non-critical output (same as --log-level warning).",
    )
    log_level_validate.add_argument(
        "-v",
        "--verbose",
        action="store_const",
        const="debug",
        dest="log_level",
        help="Verbose output (same as --log-level debug).",
    )
    log_level_validate.add_argument(
        "--log-level",
        choices=LEVEL_ORDER,
        default=None,
        dest="log_level",
        help="Set log verbosity level.",
    )

    # Watch command
    watch_parser = subparsers.add_parser(
        "watch",
        help="Watch for changes and rebuild automatically",
    )
    watch_parser.add_argument(
        "source",
        nargs="+",
        help="Source package directories to watch",
    )
    watch_parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output file path for the zipapp",
    )
    watch_parser.add_argument(
        "-m",
        "--main",
        dest="entry_point",
        help="Entry point (module:function or module)",
    )
    watch_parser.add_argument(
        "-p",
        "--python",
        dest="shebang",
        help="Shebang line (interpreter path)",
    )
    watch_parser.add_argument(
        "--compress",
        action="store_true",
        help="Compress the zip file",
    )
    watch_parser.add_argument(
        "--exclude",
        nargs="+",
        help="Exclude patterns (glob patterns)",
    )
    watch_parser.add_argument(
        "--interval",
        type=float,
        default=None,
        help="Watch interval in seconds (default: 1.0)",
    )
    watch_parser.add_argument(
        "--main-guard",
        action="store_true",
        default=True,
        dest="main_guard",
        help="Wrap entry point in 'if __name__ == \"__main__\":' guard (default: True)",
    )
    watch_parser.add_argument(
        "--no-main-guard",
        action="store_false",
        dest="main_guard",
        help="Do not wrap entry point in main guard",
    )

    # Add log level options to watch parser
    log_level_watch = watch_parser.add_mutually_exclusive_group()
    log_level_watch.add_argument(
        "-q",
        "--quiet",
        action="store_const",
        const="warning",
        dest="log_level",
        help="Suppress non-critical output (same as --log-level warning).",
    )
    log_level_watch.add_argument(
        "-v",
        "--verbose",
        action="store_const",
        const="debug",
        dest="log_level",
        help="Verbose output (same as --log-level debug).",
    )
    log_level_watch.add_argument(
        "--log-level",
        choices=LEVEL_ORDER,
        default=None,
        dest="log_level",
        help="Set log verbosity level.",
    )

    return parser


def main(args: list[str] | None = None) -> int:  # noqa: PLR0911, PLR0912
    """Main entry point for the zipbundler CLI."""
    logger = getAppLogger()

    parser = _setup_parser()

    # --- Handle --info flag early (before subcommand parsing) ---
    # This avoids conflicts with subcommand parsing
    if args and "--info" in args:
        # Extract source from args (everything that's not a flag and not a command)
        source: str | None = None
        filtered_args: list[str] = []
        commands = {"init", "list", "validate", "watch"}
        for arg in args:
            if arg == "--info" or arg.startswith("-"):
                filtered_args.append(arg)
            elif arg not in commands:
                # This is likely the source path
                if source is None:
                    source = arg
                # Don't add it to filtered_args to avoid subcommand conflict
            else:
                # It's a command, don't process as --info
                filtered_args.append(arg)
        # Parse known args to get --info flag and other flags (without source)
        parsed_args, _remaining = parser.parse_known_args(filtered_args)
        # Initialize logger with CLI args
        resolved_log_level = logger.determineLogLevel(args=parsed_args)
        logger.setLevel(resolved_log_level)
        # Handle early exits
        early_exit_code = _handle_early_exits(parsed_args)
        if early_exit_code is not None:
            return early_exit_code
        # Handle --info with extracted source
        return handle_info_command(source, parser)

    parsed_args = parser.parse_args(args)

    # Initialize logger with CLI args
    resolved_log_level = logger.determineLogLevel(args=parsed_args)
    logger.setLevel(resolved_log_level)

    # --- Handle early exits (version, etc.) ---
    early_exit_code = _handle_early_exits(parsed_args)
    if early_exit_code is not None:
        return early_exit_code

    # --- Handle subcommands ---
    if parsed_args.command == "build":
        return handle_build_command(parsed_args)
    if parsed_args.command == "init":
        return handle_init_command(parsed_args)
    if parsed_args.command == "list":
        return handle_list_command(parsed_args)
    if parsed_args.command == "validate":
        return handle_validate_command(parsed_args)
    if parsed_args.command == "watch":
        return handle_watch_command(parsed_args)

    # No command provided and no zipapp-style usage
    if not parsed_args.source:
        parser.error("No command specified. Use --help for usage.")
        return 1  # pragma: no cover
    # SOURCE provided but no --info, this would be for building (not yet implemented)
    parser.error(
        "Building from SOURCE is not yet implemented. "
        "Use 'zipbundler build' or 'zipbundler list' commands."
    )
    return 1  # pragma: no cover


if __name__ == "__main__":
    sys.exit(main())
