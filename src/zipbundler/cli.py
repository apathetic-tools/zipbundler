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
from .constants import DEFAULT_DRY_RUN, DEFAULT_WATCH_INTERVAL
from .logs import getAppLogger
from .meta import DESCRIPTION, PROGRAM_DISPLAY, PROGRAM_PACKAGE, PROGRAM_SCRIPT


# --------------------------------------------------------------------------- #
# CLI setup and helpers
# --------------------------------------------------------------------------- #


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


def _setup_parser() -> argparse.ArgumentParser:  # noqa: PLR0915
    """Define and return the CLI argument parser."""
    parser = HintingArgumentParser(
        prog=PROGRAM_SCRIPT,
        description=DESCRIPTION,
    )

    # --- Commands ---
    commands = parser.add_argument_group("Commands")

    # build (default)
    #    invalidated by: info, list, validate
    #    can be used with: watch, init
    #    not valid with: version, selftest, help
    commands.add_argument(
        "--build",
        action="store_true",
        help="Build archive from current directory or config file. (default)",
    )

    # watch (rebuild automatically)
    #    implies build
    #   can be used with: build, info, list, validate
    #     not affected by: init
    #    not valid with: version, selftest, help
    commands.add_argument(
        "-w",
        "--watch",
        nargs="?",
        type=float,
        metavar="SECONDS",
        default=None,
        help=(
            "Rebuild automatically on changes. "
            "Optionally specify interval in seconds"
            f" (default config or: {DEFAULT_WATCH_INTERVAL}). "
        ),
    )

    # info (display interpreter + metadata)
    #    invalidates: build
    #    can be used with: watch, init, list, validate
    #    not valid with: version, selftest, help
    commands.add_argument(
        "--info",
        default=False,
        action="store_true",
        help="Display the interpreter + metadata.",
    )

    # init (create default config file)
    #   does not imply build
    #    can be used with: build, watch, info, list, validate
    #   not valid with: version, selftest, help
    commands.add_argument(
        "--init",
        action="store_true",
        help=f"Create a .{PROGRAM_PACKAGE}.jsonc config file from defaults and args.",
    )

    # list (display packages and files)
    #    invalidates: build
    #   can be used with: watch, info, init, validate
    #    not valid with: version, selftest, help
    commands.add_argument(
        "-l",
        "--list",
        action="store_true",
        help="List packages and files.",
    )

    # validate (configuration file)
    #    invalidates: build
    #   can be used with: watch, info, init, list
    #    not valid with: version, selftest, help
    commands.add_argument(
        "--validate",
        action="store_true",
        help=(
            "Validate configuration file and resolved settings without "
            "executing a build. Validates config syntax, file collection, "
            "and path resolution (includes CLI arguments and environment variables)."
        ),
    )

    # selftest
    #    invalidates: all
    #   not valid with: version, help
    commands.add_argument(
        "--selftest",
        action="store_true",
        help="Run a built-in sanity test to verify tool correctness.",
    )

    # version
    #    invalidates: all
    #    not valid with: selftest, help
    commands.add_argument("--version", action="store_true", help="Show version info.")

    # --- Build flags ---
    build_flags = parser.add_argument_group("Build flags")

    # includes
    build_flags.add_argument(  # positional
        "include",
        action="extend",
        nargs="*",
        metavar="INCLUDE",
        help="Source directory, file, or glob pattern (shorthand for --include).",
    )
    build_flags.add_argument(
        "-i",
        "--include",
        action="extend",
        nargs="+",
        metavar="PATH",
        dest="include",
        help="Override include paths. Format: path or path:dest",
    )
    build_flags.add_argument(  # convenience alias
        "-s",
        "--source",
        action="extend",
        nargs="+",
        dest="include",
        help=argparse.SUPPRESS,
    )

    # additional includes (CLI only, not available in config files)
    build_flags.add_argument(
        "--add-include",
        action="extend",
        nargs="+",
        metavar="PATH",
        dest="add_include",
        help=(
            "Additional include paths to append to config includes (CLI only). "
            "Format: path or path:dest. Supports files and directories. "
            "Relative to current working directory."
        ),
    )

    # add-zip
    build_flags.add_argument(
        "--add-zip",
        action="extend",
        nargs="+",
        metavar="PATH",
        dest="add_zip",
        help=(
            "Add zip file contents to the output (CLI only, highest priority). "
            "Format: path or path:dest. Merges the zip's contents into the "
            "output, with optional destination remapping. "
            "Relative to current working directory."
        ),
    )

    # excludes
    build_flags.add_argument(
        "-e",
        "--exclude",
        action="extend",
        nargs="+",
        metavar="PATH",
        dest="exclude",
        help=(
            "Override exclude patterns. Format: path directory, file, or glob pattern."
        ),
    )

    # additional excludes
    build_flags.add_argument(
        "--add-exclude",
        action="extend",
        nargs="+",
        metavar="PATH",
        dest="add_exclude",
        help="Additional exclude patterns (relative to cwd). Extends config excludes.",
    )

    # output
    build_flags.add_argument(
        "-o",
        "--output",
        dest="output",
        default=None,
        help=(
            "Override the name of the output file or directory. "
            "Use trailing slash for directories (e.g., 'dist/'), "
            "otherwise treated as file. "
            "Examples: 'dist/project.py' (file) or 'bin/' (directory)."
        ),
    )
    build_flags.add_argument(  # convenience alias
        "--out", dest="output", help=argparse.SUPPRESS
    )

    # input
    build_flags.add_argument(
        "--input",
        dest="input",
        default=None,
        help=(
            "Override the name of the input file or directory. "
            "Start from an existing build (usually optional)"
            "Examples: 'dist/project.py' (file) or 'bin/' (directory)."
        ),
    )
    build_flags.add_argument(  # convenience alias
        "--in",
        dest="input",  # note: args.in is reserved
        help=argparse.SUPPRESS,
    )

    # input mode (append vs replace)
    input_mode = build_flags.add_mutually_exclusive_group()
    input_mode.add_argument(
        "-a",
        "--append",
        dest="input_mode",
        action="store_const",
        const="append",
        help=(
            "Append to input archive (default). Merge config packages "
            "with existing files."
        ),
    )
    input_mode.add_argument(
        "-r",
        "--replace",
        dest="input_mode",
        action="store_const",
        const="replace",
        help=(
            "Replace input archive contents. Use config packages as new base, "
            "discard old."
        ),
    )
    input_mode.set_defaults(input_mode="append")

    # config
    build_flags.add_argument("--config", help="Path to build config file.")

    # --- Build options ---
    build_opts = parser.add_argument_group("Build & Watch options")

    # dry-run
    build_opts.add_argument(
        "--dry-run",
        action="store_true",
        default=DEFAULT_DRY_RUN,
        help=(
            "Simulate build actions without copying or deleting files "
            f"(default: {DEFAULT_DRY_RUN})."
        ),
    )

    # gitignore behavior
    gitignore = build_opts.add_mutually_exclusive_group()
    gitignore.add_argument(
        "--gitignore",
        dest="respect_gitignore",
        action="store_true",
        help="Respect .gitignore when selecting files (default).",
    )
    gitignore.add_argument(
        "--no-gitignore",
        dest="respect_gitignore",
        action="store_false",
        help="Ignore .gitignore and include all files.",
    )
    gitignore.set_defaults(respect_gitignore=None)

    # shebang
    shebang = build_opts.add_mutually_exclusive_group()
    shebang.add_argument(
        "-p",
        "--shebang",
        "--python",
        dest="shebang",
        default=None,
        help="The name of the Python interpreter to use (default: auto decide).",
    )
    shebang.add_argument(
        "--no-shebang",
        action="store_false",
        dest="shebang",
        help="Disable shebang insertion",
    )

    # main
    main = build_opts.add_mutually_exclusive_group()
    main.add_argument(
        "-m",
        "--main",
        dest="entry_point",
        default=None,
        help=("The main function of the application (default: auto decide)."),
    )
    main.add_argument(
        "--no-main",
        action="store_false",
        dest="entry_point",
        help="Disable main insertion.",
    )

    # main mode
    build_opts.add_argument(
        "--main-mode",
        dest="main_mode",
        default=None,
        help=(
            "Mode for main function detection (default: 'auto'). "
            "Set via config or environment variable MAIN_MODE."
        ),
    )

    # main name
    build_opts.add_argument(
        "--main-name",
        dest="main_name",
        default=None,
        help=(
            "Name to use for main function (default: None, auto-detect). "
            "Set via config or environment variable MAIN_NAME."
        ),
    )

    # compress
    compress = build_opts.add_mutually_exclusive_group()
    compress.add_argument(
        "-c",
        "--compress",
        action="store_true",
        dest="compress",
        default=None,
        help=(
            "Compress files with the deflate method. "
            "Files are stored uncompressed by default."
        ),
    )
    compress.add_argument(
        "--no-compress",
        action="store_false",
        dest="compress",
        default=None,
        help="Do not compress the zip file (for --build, overrides config)",
    )

    # compress level
    build_opts.add_argument(
        "--compression-level",
        type=int,
        dest="compress_level",
        help="Compression level for deflate method (0-9, only used with --compress)",
    )

    # timestamps
    build_opts.add_argument(
        "--disable-build-timestamp",
        action="store_true",
        help="Disable build timestamps for deterministic builds (uses placeholder).",
    )

    # --- Universal flags ---
    uni = parser.add_argument_group("Universal flags")

    # force (overwrite)
    uni.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Overwrite existing file.",
    )

    # strict (configuration)
    uni.add_argument(
        "--strict",
        action="store_true",
        help="Fail on config validation warnings",
    )

    # compat (compatability)
    uni.add_argument(
        "--compat",
        action="store_true",
        dest="compat",
        help="Compatability mode with Stdlib zipapp behaviour",
    )
    uni.add_argument(  # convenience alias
        "--compatability",
        action="store_true",
        dest="compat",
        help=argparse.SUPPRESS,
    )

    # --- Terminal flags ---
    term = parser.add_argument_group("Terminal flags")

    # color
    color = term.add_mutually_exclusive_group()
    color.add_argument(
        "--no-color",
        dest="use_color",
        action="store_const",
        const=False,
        help="Disable ANSI color output.",
    )
    color.add_argument(
        "--color",
        dest="use_color",
        action="store_const",
        const=True,
        help="Force-enable ANSI color output (overrides auto-detect).",
    )
    color.set_defaults(use_color=None)

    # verbosity
    log_level = term.add_mutually_exclusive_group()

    #     quiet
    log_level.add_argument(
        "-q",
        "--quiet",
        action="store_const",
        const="warning",
        dest="log_level",
        help="Suppress non-critical output (same as --log-level warning).",
    )

    #     brief
    log_level.add_argument(
        "-b",
        "--brief",
        action="store_const",
        const="brief",
        dest="log_level",
        help="Show brief output (same as --log-level brief).",
    )

    #     detail
    log_level.add_argument(
        "-d",
        "--detail",
        action="store_const",
        const="detail",
        dest="log_level",
        help="Show detailed output (same as --log-level detail).",
    )

    #    verbose
    log_level.add_argument(
        "-v",
        "--verbose",
        action="store_const",
        const="debug",
        dest="log_level",
        help="Verbose output (same as --log-level debug).",
    )

    #    log-level
    log_level.add_argument(
        "--log-level",
        choices=LEVEL_ORDER,
        default=None,
        dest="log_level",
        help="Set log verbosity level.",
    )

    return parser


def _prepare_init_args(parsed_args: argparse.Namespace) -> argparse.Namespace:
    """Prepare arguments for init command."""
    init_args = argparse.Namespace()
    # Use --config to specify where to create the config file
    init_args.config = getattr(parsed_args, "config", None)
    init_args.force = getattr(parsed_args, "force", False)
    init_args.log_level = parsed_args.log_level
    return init_args


def _prepare_build_args(parsed_args: argparse.Namespace) -> argparse.Namespace:
    """Prepare arguments for build command."""
    build_args = argparse.Namespace()
    build_args.config = parsed_args.config
    build_args.output = parsed_args.output
    build_args.input = parsed_args.input
    build_args.input_mode = getattr(parsed_args, "input_mode", "append")
    build_args.entry_point = parsed_args.entry_point
    build_args.main_mode = getattr(parsed_args, "main_mode", None)
    build_args.main_name = getattr(parsed_args, "main_name", None)
    build_args.shebang = parsed_args.shebang
    # Handle --compress, --no-compress, and compression_level
    if hasattr(parsed_args, "compress") and parsed_args.compress is False:
        # --no-compress was explicitly set
        build_args.compress = False
    elif hasattr(parsed_args, "compress") and parsed_args.compress is True:
        # --compress was set
        build_args.compress = True
    else:
        # Neither flag was set, let config file decide
        build_args.compress = None
    build_args.compression_level = getattr(parsed_args, "compress_level", None)
    build_args.include = getattr(parsed_args, "include", None)
    build_args.add_include = getattr(parsed_args, "add_include", None)
    build_args.add_zip = getattr(parsed_args, "add_zip", None)
    build_args.exclude = getattr(parsed_args, "exclude", None)
    build_args.add_exclude = getattr(parsed_args, "add_exclude", None)
    build_args.respect_gitignore = getattr(parsed_args, "respect_gitignore", None)
    # main_guard removed (handled via config)
    build_args.disable_build_timestamp = getattr(
        parsed_args, "disable_build_timestamp", None
    )
    build_args.dry_run = getattr(parsed_args, "dry_run", False)
    build_args.force = getattr(parsed_args, "force", False)
    build_args.strict = getattr(parsed_args, "strict", False)
    build_args.log_level = parsed_args.log_level
    return build_args


def _prepare_list_args(parsed_args: argparse.Namespace) -> argparse.Namespace:
    """Prepare arguments for list command."""
    list_args = argparse.Namespace()
    # Include is now always a list from nargs="*"
    list_args.include = parsed_args.include if parsed_args.include else []
    list_args.log_level = parsed_args.log_level
    return list_args


def _prepare_validate_args(parsed_args: argparse.Namespace) -> argparse.Namespace:
    """Prepare arguments for validate command."""
    validate_args = argparse.Namespace()
    validate_args.config = getattr(parsed_args, "config", None)
    validate_args.strict = getattr(parsed_args, "strict", False)
    validate_args.log_level = parsed_args.log_level
    return validate_args


def _prepare_watch_args(parsed_args: argparse.Namespace) -> argparse.Namespace:
    """Prepare arguments for watch command."""
    watch_args = argparse.Namespace()
    # Include is now always a list from nargs="*"
    watch_args.include = parsed_args.include if parsed_args.include else []
    watch_args.output = parsed_args.output
    watch_args.entry_point = parsed_args.entry_point
    watch_args.main_mode = getattr(parsed_args, "main_mode", None)
    watch_args.main_name = getattr(parsed_args, "main_name", None)
    watch_args.shebang = parsed_args.shebang
    watch_args.compress = parsed_args.compress
    watch_args.exclude = getattr(parsed_args, "exclude", None)
    watch_args.add_exclude = getattr(parsed_args, "add_exclude", None)
    watch_args.respect_gitignore = getattr(parsed_args, "respect_gitignore", None)
    watch_args.disable_build_timestamp = getattr(
        parsed_args, "disable_build_timestamp", None
    )
    watch_args.watch = parsed_args.watch  # Can be float or None
    # main_guard removed (handled via config)
    watch_args.log_level = parsed_args.log_level
    return watch_args


def main(args: list[str] | None = None) -> int:  # noqa: PLR0911, PLR0912, C901
    """Main entry point for the zipbundler CLI (zipapp-style only)."""
    logger = getAppLogger()

    parser = _setup_parser()
    parsed_args = parser.parse_args(args)

    # Initialize logger with CLI args
    resolved_log_level = logger.determineLogLevel(args=parsed_args)
    logger.setLevel(resolved_log_level)

    # Initialize color output based on CLI args
    use_color = getattr(parsed_args, "use_color", None)
    if use_color is not None:
        logger.enable_color = use_color
    else:
        logger.enable_color = logger.determineColorEnabled()

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
        if not parsed_args.include:
            parser.error("SOURCE is required for --list")
            return 1  # pragma: no cover (parser.error raises SystemExit)
        return handle_list_command(_prepare_list_args(parsed_args))

    if parsed_args.validate:
        return handle_validate_command(_prepare_validate_args(parsed_args))

    if parsed_args.watch:
        if not parsed_args.include:
            parser.error("SOURCE is required for --watch")
            return 1  # pragma: no cover (parser.error raises SystemExit)
        if not parsed_args.output:
            parser.error("Output file (-o/--output) is required for --watch")
            return 1  # pragma: no cover (parser.error raises SystemExit)
        return handle_watch_command(_prepare_watch_args(parsed_args))

    # --- Handle --info flag ---
    if parsed_args.info:
        if not parsed_args.include:
            parser.error("SOURCE is required for --info")
            return 1  # pragma: no cover (parser.error raises SystemExit)
        # Info command expects a single source (first one)
        # Include is always a list from nargs="*"
        source = parsed_args.include[0]
        return handle_info_command(source, parser)

    # --- Handle zipapp-style building (default) ---
    if not parsed_args.include:
        parser.error("SOURCE is required")
        return 1  # pragma: no cover (parser.error raises SystemExit)

    # Validate zipapp-style requirements
    if not parsed_args.output:
        logger.error("Output file (-o/--output) is required when using SOURCE")
        return 1

    # Zipapp-style expects a single source (take first from list)
    if len(parsed_args.include) > 1:
        logger.error("Only one SOURCE is allowed for zipapp-style building")
        return 1

    # Create a modified args object with single source string
    zipapp_args = argparse.Namespace(**vars(parsed_args))
    zipapp_args.include = parsed_args.include[0]

    # This is zipapp-style building
    return handle_zipapp_style_command(zipapp_args)


if __name__ == "__main__":
    sys.exit(main())
