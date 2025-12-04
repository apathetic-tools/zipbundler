import argparse
import sys
from difflib import get_close_matches

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
    handle_zipapp_style_command,
)
from .logs import getAppLogger
from .meta import PROGRAM_DISPLAY, PROGRAM_PACKAGE, PROGRAM_SCRIPT


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


class HintingArgumentParser(argparse.ArgumentParser):
    """Argument parser that provides helpful hints for mistyped arguments."""

    def error(self, message: str) -> None:  # type: ignore[override]
        """Override error to provide hints for unrecognized arguments."""
        # Build known option strings: ["-v", "--verbose", "--log-level", ...]
        known_opts: list[str] = []
        for action in self._actions:
            known_opts.extend([s for s in action.option_strings if s])

        hint_lines: list[str] = []
        # Argparse message for bad flags is typically
        # "unrecognized arguments: --inclde ..."
        if "unrecognized arguments:" in message:
            bad = message.split("unrecognized arguments:", 1)[1].strip()
            # Split conservatively on whitespace
            bad_args = [tok for tok in bad.split() if tok.startswith("-")]
            for arg in bad_args:
                close = get_close_matches(arg, known_opts, n=1, cutoff=0.6)
                if close:
                    hint_lines.append(f"Hint: did you mean {close[0]}?")

        # Print usage + the original error
        self.print_usage(sys.stderr)
        full = f"{self.prog}: error: {message}"
        if hint_lines:
            full += "\n" + "\n".join(hint_lines)
        self.exit(2, full + "\n")


def _setup_parser() -> argparse.ArgumentParser:
    """Define and return the CLI argument parser (zipapp-style only)."""
    parser = HintingArgumentParser(
        prog=PROGRAM_SCRIPT,
        description="Bundle your packages into a runnable, importable zip",
    )

    # Version flag
    parser.add_argument("--version", action="store_true", help="Show version info.")

    # zipapp-style options (matching python -m zipapp interface)
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="The name of the output archive. Required if SOURCE is an archive.",
    )
    parser.add_argument(
        "--python",
        "-p",
        dest="shebang",
        default=None,
        help="The name of the Python interpreter to use (default: no shebang line).",
    )
    parser.add_argument(
        "--no-shebang",
        action="store_false",
        dest="shebang",
        help="Disable shebang insertion",
    )
    parser.add_argument(
        "--main",
        "-m",
        dest="entry_point",
        default=None,
        help=(
            "The main function of the application "
            "(default: use an existing __main__.py)."
        ),
    )
    parser.add_argument(
        "--compress",
        "-c",
        action="store_true",
        help=(
            "Compress files with the deflate method. "
            "Files are stored uncompressed by default."
        ),
    )
    parser.add_argument(
        "--build-no-compress",
        action="store_false",
        dest="build_compress",
        default=None,
        help="Do not compress the zip file (for --build, overrides config)",
    )
    parser.add_argument(
        "--compression-level",
        type=int,
        dest="compression_level",
        help="Compression level for deflate method (0-9, only used with --compress)",
    )
    parser.add_argument(
        "--info",
        default=False,
        action="store_true",
        help="Display the interpreter from the archive.",
    )

    # Command flags (take over execution like --info and --version)
    parser.add_argument(
        "--init",
        action="store_true",
        help="Create a default .zipbundler.jsonc config file.",
    )
    parser.add_argument(
        "--build",
        action="store_true",
        help="Build zip from current directory or config file.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List packages and files that would be included in the bundle.",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate configuration file.",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch for changes and rebuild automatically.",
    )

    # Arguments for command flags
    # --init arguments
    parser.add_argument(
        "--init-output",
        help="Output path for config file (default: .zipbundler.jsonc)",
    )
    parser.add_argument(
        "--init-force",
        action="store_true",
        help="Overwrite existing config file (for --init).",
    )
    parser.add_argument(
        "--init-preset",
        default="basic",
        help=(
            "Use a preset template: basic, cli, library, or minimal "
            "(for --init, default: basic)"
        ),
    )
    parser.add_argument(
        "--init-list-presets",
        action="store_true",
        help="List available preset templates (for --init).",
    )

    # --build arguments
    parser.add_argument(
        "--build-config",
        help="Path to configuration file (for --build)",
    )
    parser.add_argument(
        "--build-packages",
        nargs="+",
        help="Package patterns to include (for --build, overrides config)",
    )
    parser.add_argument(
        "--build-exclude",
        nargs="+",
        help="Exclude patterns (for --build, overrides config)",
    )
    parser.add_argument(
        "--build-main-guard",
        action="store_true",
        default=None,
        help="Wrap entry point in main guard (for --build, overrides config)",
    )
    parser.add_argument(
        "--build-no-main-guard",
        action="store_false",
        dest="build_main_guard",
        help="Do not wrap entry point in main guard (for --build)",
    )
    parser.add_argument(
        "--build-dry-run",
        action="store_true",
        help="Preview what would be bundled without creating zip (for --build)",
    )
    parser.add_argument(
        "--build-force",
        action="store_true",
        help="Force rebuild even if output is up-to-date (for --build)",
    )
    parser.add_argument(
        "--build-strict",
        action="store_true",
        help="Fail on config validation warnings (for --build)",
    )

    # --list arguments
    parser.add_argument(
        "--list-tree",
        action="store_true",
        help="Show as directory tree (for --list)",
    )
    parser.add_argument(
        "--list-count",
        action="store_true",
        help="Show file count only (for --list)",
    )

    # --validate arguments
    parser.add_argument(
        "--validate-config",
        help="Path to configuration file (for --validate)",
    )
    parser.add_argument(
        "--validate-strict",
        action="store_true",
        help="Fail on warnings (for --validate)",
    )

    # --watch arguments
    parser.add_argument(
        "--watch-interval",
        type=float,
        default=None,
        help="Watch interval in seconds (for --watch, default: 1.0)",
    )
    parser.add_argument(
        "--watch-exclude",
        nargs="+",
        help="Exclude patterns for watch (for --watch)",
    )
    parser.add_argument(
        "--watch-main-guard",
        action="store_true",
        default=True,
        help="Wrap entry point in main guard (for --watch, default: True)",
    )
    parser.add_argument(
        "--watch-no-main-guard",
        action="store_false",
        dest="watch_main_guard",
        help="Do not wrap entry point in main guard (for --watch)",
    )

    # Log level options
    log_level_group = parser.add_mutually_exclusive_group()
    log_level_group.add_argument(
        "-q",
        "--quiet",
        action="store_const",
        const="warning",
        dest="log_level",
        help="Suppress non-critical output (same as --log-level warning).",
    )
    log_level_group.add_argument(
        "-v",
        "--verbose",
        action="store_const",
        const="debug",
        dest="log_level",
        help="Verbose output (same as --log-level debug).",
    )
    log_level_group.add_argument(
        "--log-level",
        choices=LEVEL_ORDER,
        default=None,
        dest="log_level",
        help="Set log verbosity level.",
    )

    # Source positional argument (like zipapp)
    # Use nargs="*" to support multiple sources for --list and --watch
    parser.add_argument(
        "source",
        nargs="*",
        help="Source directory (or existing archive).",
    )

    return parser


def _prepare_init_args(parsed_args: argparse.Namespace) -> argparse.Namespace:
    """Prepare arguments for init command."""
    init_args = argparse.Namespace()
    init_args.output = parsed_args.init_output
    init_args.force = parsed_args.init_force
    init_args.preset = parsed_args.init_preset
    init_args.list_presets = parsed_args.init_list_presets
    init_args.log_level = parsed_args.log_level
    return init_args


def _prepare_build_args(parsed_args: argparse.Namespace) -> argparse.Namespace:
    """Prepare arguments for build command."""
    build_args = argparse.Namespace()
    build_args.config = parsed_args.build_config
    build_args.output = parsed_args.output
    build_args.entry_point = parsed_args.entry_point
    build_args.shebang = parsed_args.shebang
    # Handle compress: use --build-no-compress if set, otherwise use --compress
    # --build-no-compress takes precedence over --compress
    if parsed_args.build_compress is False:
        # --build-no-compress was explicitly set
        build_args.compress = False
    elif parsed_args.compress:
        # --compress was set
        build_args.compress = True
    else:
        # Neither flag was set, let config file decide
        build_args.compress = None
    build_args.compression_level = parsed_args.compression_level
    build_args.packages = parsed_args.build_packages
    build_args.exclude = parsed_args.build_exclude
    build_args.main_guard = parsed_args.build_main_guard
    build_args.dry_run = parsed_args.build_dry_run
    build_args.force = parsed_args.build_force
    build_args.strict = parsed_args.build_strict
    build_args.log_level = parsed_args.log_level
    return build_args


def _prepare_list_args(parsed_args: argparse.Namespace) -> argparse.Namespace:
    """Prepare arguments for list command."""
    list_args = argparse.Namespace()
    # Source is now always a list from nargs="*"
    list_args.source = parsed_args.source if parsed_args.source else []
    list_args.tree = parsed_args.list_tree
    list_args.count = parsed_args.list_count
    list_args.log_level = parsed_args.log_level
    return list_args


def _prepare_validate_args(parsed_args: argparse.Namespace) -> argparse.Namespace:
    """Prepare arguments for validate command."""
    validate_args = argparse.Namespace()
    validate_args.config = parsed_args.validate_config
    validate_args.strict = parsed_args.validate_strict
    validate_args.log_level = parsed_args.log_level
    return validate_args


def _prepare_watch_args(parsed_args: argparse.Namespace) -> argparse.Namespace:
    """Prepare arguments for watch command."""
    watch_args = argparse.Namespace()
    # Source is now always a list from nargs="*"
    watch_args.source = parsed_args.source if parsed_args.source else []
    watch_args.output = parsed_args.output
    watch_args.entry_point = parsed_args.entry_point
    watch_args.shebang = parsed_args.shebang
    watch_args.compress = parsed_args.compress
    watch_args.exclude = parsed_args.watch_exclude
    watch_args.interval = parsed_args.watch_interval
    watch_args.main_guard = parsed_args.watch_main_guard
    watch_args.log_level = parsed_args.log_level
    return watch_args


def main(args: list[str] | None = None) -> int:  # noqa: PLR0911, PLR0912
    """Main entry point for the zipbundler CLI (zipapp-style only)."""
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

    # --- Handle command flags (take over execution) ---
    # These are handled in priority order

    if parsed_args.init:
        return handle_init_command(_prepare_init_args(parsed_args))

    if parsed_args.build:
        return handle_build_command(_prepare_build_args(parsed_args))

    if parsed_args.list:
        if not parsed_args.source:
            parser.error("SOURCE is required for --list")
            return 1  # pragma: no cover (parser.error raises SystemExit)
        return handle_list_command(_prepare_list_args(parsed_args))

    if parsed_args.validate:
        return handle_validate_command(_prepare_validate_args(parsed_args))

    if parsed_args.watch:
        if not parsed_args.source:
            parser.error("SOURCE is required for --watch")
            return 1  # pragma: no cover (parser.error raises SystemExit)
        if not parsed_args.output:
            parser.error("Output file (-o/--output) is required for --watch")
            return 1  # pragma: no cover (parser.error raises SystemExit)
        return handle_watch_command(_prepare_watch_args(parsed_args))

    # --- Handle --info flag ---
    if parsed_args.info:
        if not parsed_args.source:
            parser.error("SOURCE is required for --info")
            return 1  # pragma: no cover (parser.error raises SystemExit)
        # Info command expects a single source (first one)
        # Source is always a list from nargs="*"
        source = parsed_args.source[0]
        return handle_info_command(source, parser)

    # --- Handle zipapp-style building (default) ---
    if not parsed_args.source:
        parser.error("SOURCE is required")
        return 1  # pragma: no cover (parser.error raises SystemExit)

    # Validate zipapp-style requirements
    if not parsed_args.output:
        logger.error("Output file (-o/--output) is required when using SOURCE")
        return 1

    # Zipapp-style expects a single source (take first from list)
    if len(parsed_args.source) > 1:
        logger.error("Only one SOURCE is allowed for zipapp-style building")
        return 1

    # Create a modified args object with single source string
    zipapp_args = argparse.Namespace(**vars(parsed_args))
    zipapp_args.source = parsed_args.source[0]

    # This is zipapp-style building
    return handle_zipapp_style_command(zipapp_args)


if __name__ == "__main__":
    sys.exit(main())
