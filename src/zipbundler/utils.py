"""Utility functions for path resolution and include handling."""

import argparse
from pathlib import Path

from apathetic_utils import cast_hint

from zipbundler.config.config_types import IncludeResolved, OriginType, PathResolved
from zipbundler.constants import DEFAULT_COMPRESS, DEFAULT_RESPECT_GITIGNORE
from zipbundler.logs import getAppLogger


def make_include_resolved(
    path: Path | str,
    root: Path,
    origin: OriginType,
    *,
    dest: Path | None = None,
    pattern: str | None = None,
) -> IncludeResolved:
    """Create an IncludeResolved dictionary.

    Args:
        path: File or directory path (absolute or relative to root)
        root: Root directory for resolving relative paths
        origin: Source of the include (cli or config)
        dest: Optional custom destination in the output zip
        pattern: Original pattern before resolution (for logging)

    Returns:
        IncludeResolved dictionary
    """
    # Build result dict with optional fields only when present
    result_dict: dict[str, object] = {
        "path": path,
        "root": root,
        "origin": origin,
    }
    if pattern is not None:
        result_dict["pattern"] = pattern
    if dest is not None:
        result_dict["dest"] = dest

    return result_dict  # type: ignore[return-value]


def parse_include_with_dest(
    raw: str, context_root: Path
) -> tuple[IncludeResolved, bool]:
    """Parse include string with optional :dest suffix.

    Handles the "path:dest" format where path and dest are separated by a colon.
    Special handling for Windows drive letters (e.g., C:, D:).
    Paths are resolved relative to context_root.

    Args:
        raw: Raw include string, may contain ":dest" suffix
        context_root: Root directory for path resolution (cwd for CLI args)

    Returns:
        Tuple of (IncludeResolved, has_dest) where has_dest indicates
        if a destination was parsed from the input. The IncludeResolved
        has origin="cli".
    """
    has_dest = False
    path_str = raw
    dest_str: str | None = None

    # Handle "path:dest" format - split on last colon
    if ":" in raw:
        parts = raw.rsplit(":", 1)
        path_part, dest_part = parts[0], parts[1]

        # Check if this is a Windows drive letter (C:, D:, etc.)
        # Drive letters are 1-2 chars, possibly with backslash
        is_drive_letter = len(path_part) <= 2 and (  # noqa: PLR2004
            len(path_part) == 1 or path_part.endswith("\\")
        )

        if not is_drive_letter:
            # Valid dest separator found
            path_str = path_part
            dest_str = dest_part
            has_dest = True

    # Normalize the path: resolve relative paths to absolute
    full_path = (context_root / path_str).resolve()
    root = context_root.resolve()

    # Create IncludeResolved with origin="cli" (from --include or --add-include)
    inc = make_include_resolved(
        full_path,
        root,
        "cli",
        pattern=raw,
    )

    # Add destination if specified
    if dest_str:
        inc["dest"] = Path(dest_str)

    return inc, has_dest


def _resolve_config_includes(
    include_list: list[object], config_dir: Path
) -> list[IncludeResolved]:
    """Resolve includes from config file (relative to config_dir).

    Args:
        include_list: Raw include list from config
        config_dir: Directory of config file

    Returns:
        List of resolved includes with origin="config"
    """
    includes: list[IncludeResolved] = []

    for raw in include_list:
        if isinstance(raw, dict):
            # Object format: {"path": "...", "dest": "..."}
            raw_dict: dict[str, object] = cast_hint(dict[str, object], raw)
            path_obj = raw_dict.get("path", "")
            if not isinstance(path_obj, str):
                continue
            path_str: str = path_obj
            dest_obj = raw_dict.get("dest")
            dest_str: str | None = None
            if isinstance(dest_obj, str):
                dest_str = dest_obj

            inc = make_include_resolved(
                path_str, config_dir, "config", pattern=path_str
            )
            if dest_str:
                inc["dest"] = Path(dest_str)
            includes.append(inc)
        elif isinstance(raw, str):
            # String format: "path/to/files" or "path:dest"
            inc, _ = parse_include_with_dest(raw, config_dir)
            # Override origin since this came from config, not CLI
            inc["origin"] = "config"
            includes.append(inc)

    return includes


def _resolve_cli_includes(
    include_list: list[object], cwd: Path
) -> list[IncludeResolved]:
    """Resolve includes from CLI arguments (relative to cwd).

    Args:
        include_list: Raw include list from CLI
        cwd: Current working directory

    Returns:
        List of resolved includes with origin="cli"
    """
    includes: list[IncludeResolved] = []

    for raw in include_list:
        if isinstance(raw, str):
            inc, _ = parse_include_with_dest(raw, cwd)
            includes.append(inc)

    return includes


def resolve_includes(
    raw_config: dict[str, object] | None,
    *,
    args: argparse.Namespace,
    config_dir: Path,
    cwd: Path,
) -> list[IncludeResolved]:
    """Resolve includes from both config file and CLI arguments.

    Handles the following precedence:
    1. If --include is provided (full override): use cwd as root, ignore config
    2. If config has includes: use config_dir as root for each include
    3. If --add-include is provided: append to config includes, use cwd as root

    Args:
        raw_config: Raw configuration dict from config file (may be None)
        args: Parsed command-line arguments
        config_dir: Directory of config file (used for relative paths in config)
        cwd: Current working directory (used for CLI args)

    Returns:
        List of resolved includes with proper root context
    """
    logger = getAppLogger()
    includes: list[IncludeResolved] = []

    # Case 1: --include provided (full override)
    include_arg: object = getattr(args, "include", None)
    if include_arg and isinstance(include_arg, list):
        cli_list = cast_hint(list[object], include_arg)
        logger.trace(
            "[resolve_includes] Using --include override (%d items)",
            len(cli_list),
        )
        includes.extend(_resolve_cli_includes(cli_list, cwd))

    # Case 2: includes from config file
    elif raw_config and "include" in raw_config:
        raw_include_list: object = raw_config.get("include", [])
        if isinstance(raw_include_list, list) and raw_include_list:
            cfg_list = cast_hint(list[object], raw_include_list)
            logger.trace(
                "[resolve_includes] Using config includes (%d items)",
                len(cfg_list),
            )
            includes.extend(_resolve_config_includes(cfg_list, config_dir))

    # Case 3: --add-include (extend, not override)
    add_include_arg: object = getattr(args, "add_include", None)
    if add_include_arg and isinstance(add_include_arg, list):
        cli_list_add = cast_hint(list[object], add_include_arg)
        logger.trace(
            "[resolve_includes] Adding --add-include items (%d items)",
            len(cli_list_add),
        )
        includes.extend(_resolve_cli_includes(cli_list_add, cwd))

    return includes


def make_exclude_resolved(
    path: Path | str,
    root: Path,
    origin: OriginType,
    *,
    pattern: str | None = None,
) -> PathResolved:
    """Create a PathResolved dictionary for excludes.

    Args:
        path: Exclude pattern (stays as-is, not resolved to files)
        root: Root directory for pattern matching
        origin: Source of the exclude (cli or config)
        pattern: Original pattern before resolution (for logging)

    Returns:
        PathResolved dictionary
    """
    result_dict: dict[str, object] = {
        "path": path,  # Keep as string pattern, not resolved
        "root": root,
        "origin": origin,
    }
    if pattern is not None:
        result_dict["pattern"] = pattern

    return result_dict  # type: ignore[return-value]


def _resolve_config_excludes(
    exclude_list: list[object], config_dir: Path
) -> list[PathResolved]:
    """Resolve excludes from config file (relative to config_dir).

    Args:
        exclude_list: Raw exclude list from config
        config_dir: Directory of config file

    Returns:
        List of resolved excludes with origin="config"
    """
    excludes: list[PathResolved] = []

    for raw in exclude_list:
        if isinstance(raw, str):
            exc = make_exclude_resolved(raw, config_dir, "config", pattern=raw)
            excludes.append(exc)

    return excludes


def _resolve_cli_excludes(exclude_list: list[object], cwd: Path) -> list[PathResolved]:
    """Resolve excludes from CLI arguments (relative to cwd).

    Args:
        exclude_list: Raw exclude list from CLI
        cwd: Current working directory

    Returns:
        List of resolved excludes with origin="cli"
    """
    excludes: list[PathResolved] = []

    for raw in exclude_list:
        if isinstance(raw, str):
            exc = make_exclude_resolved(raw, cwd, "cli", pattern=raw)
            excludes.append(exc)

    return excludes


def resolve_excludes(
    raw_config: dict[str, object] | None,
    *,
    args: argparse.Namespace,
    config_dir: Path,
    cwd: Path,
) -> list[PathResolved]:
    """Resolve excludes from both config file and CLI arguments.

    Handles the following precedence:
    1. If --exclude is provided (full override): use cwd as root, ignore config
    2. If config has excludes: use config_dir as root for each exclude
    3. If --add-exclude is provided: append to config excludes, use cwd as root

    Args:
        raw_config: Raw configuration dict from config file (may be None)
        args: Parsed command-line arguments
        config_dir: Directory of config file (used for relative paths in config)
        cwd: Current working directory (used for CLI args)

    Returns:
        List of resolved excludes with proper root context
    """
    logger = getAppLogger()
    excludes: list[PathResolved] = []

    # Case 1: --exclude provided (full override)
    exclude_arg: object = getattr(args, "exclude", None)
    if exclude_arg and isinstance(exclude_arg, list):
        cli_list = cast_hint(list[object], exclude_arg)
        logger.trace(
            "[resolve_excludes] Using --exclude override (%d items)",
            len(cli_list),
        )
        excludes.extend(_resolve_cli_excludes(cli_list, cwd))
    else:
        # Case 2: excludes from config file
        if raw_config and "exclude" in raw_config:
            raw_exclude_list: object = raw_config.get("exclude", [])
            if isinstance(raw_exclude_list, list) and raw_exclude_list:
                cfg_list = cast_hint(list[object], raw_exclude_list)
                logger.trace(
                    "[resolve_excludes] Using config excludes (%d items)",
                    len(cfg_list),
                )
                excludes.extend(_resolve_config_excludes(cfg_list, config_dir))

        # Case 3: --add-exclude (extend, not override)
        add_exclude_arg: object = getattr(args, "add_exclude", None)
        if add_exclude_arg and isinstance(add_exclude_arg, list):
            cli_list_add = cast_hint(list[object], add_exclude_arg)
            logger.trace(
                "[resolve_excludes] Adding --add-exclude items (%d items)",
                len(cli_list_add),
            )
            excludes.extend(_resolve_cli_excludes(cli_list_add, cwd))

    return excludes


def load_gitignore_patterns(gitignore_path: Path) -> list[str]:
    """Load patterns from .gitignore file.

    Reads .gitignore and returns non-comment patterns. Skips blank lines
    and lines starting with '#'.

    Args:
        gitignore_path: Path to .gitignore file

    Returns:
        List of gitignore pattern strings
    """
    patterns: list[str] = []

    if gitignore_path.exists():
        try:
            content = gitignore_path.read_text(encoding="utf-8")
            for line in content.splitlines():
                clean_line = line.strip()
                if clean_line and not clean_line.startswith("#"):
                    patterns.append(clean_line)
        except OSError as e:
            logger = getAppLogger()
            logger.warning("Failed to read .gitignore: %s", e)

    return patterns


def resolve_gitignore(
    raw_config: dict[str, object] | None,
    *,
    args: argparse.Namespace,
) -> bool:
    """Determine whether to respect .gitignore patterns.

    Handles the following precedence (highest to lowest):
    1. CLI flag: --gitignore or --no-gitignore
    2. Config file: options.respect_gitignore
    3. Default: DEFAULT_RESPECT_GITIGNORE

    Args:
        raw_config: Raw configuration dict from config file (may be None)
        args: Parsed command-line arguments

    Returns:
        Boolean indicating whether to respect .gitignore patterns
    """
    logger = getAppLogger()

    # Case 1: CLI flag (highest priority)
    cli_flag: object = getattr(args, "respect_gitignore", None)
    if cli_flag is not None and isinstance(cli_flag, bool):
        logger.trace(
            "[resolve_gitignore] Using CLI flag: respect_gitignore=%s",
            cli_flag,
        )
        return cli_flag

    # Case 2: Config file (options.respect_gitignore)
    if raw_config:
        options: object = raw_config.get("options")
        if isinstance(options, dict):
            opts_dict = cast_hint(dict[str, object], options)
            respect_gitignore: object = opts_dict.get("respect_gitignore")
            if isinstance(respect_gitignore, bool):
                logger.trace(
                    "[resolve_gitignore] Using config: respect_gitignore=%s",
                    respect_gitignore,
                )
                return respect_gitignore

    # Case 3: Default
    logger.trace(
        "[resolve_gitignore] Using default: respect_gitignore=%s",
        DEFAULT_RESPECT_GITIGNORE,
    )
    return DEFAULT_RESPECT_GITIGNORE


def resolve_compress(
    raw_config: dict[str, object] | None,
    *,
    args: argparse.Namespace,
) -> bool:
    """Determine whether to compress the zip file.

    Handles the following precedence (highest to lowest):
    1. CLI flag: --compress or --no-compress
    2. Config file: options.compress
    3. Default: DEFAULT_COMPRESS

    Args:
        raw_config: Raw configuration dict from config file (may be None)
        args: Parsed command-line arguments

    Returns:
        Boolean indicating whether to compress the zip file
    """
    logger = getAppLogger()

    # Case 1: CLI flag (highest priority)
    cli_flag: object = getattr(args, "compress", None)
    if cli_flag is not None and isinstance(cli_flag, bool):
        logger.trace(
            "[resolve_compress] Using CLI flag: compress=%s",
            cli_flag,
        )
        return cli_flag

    # Case 2: Config file (options.compress)
    if raw_config:
        options: object = raw_config.get("options")
        if isinstance(options, dict):
            opts_dict = cast_hint(dict[str, object], options)
            compress: object = opts_dict.get("compress")
            if isinstance(compress, bool):
                logger.trace(
                    "[resolve_compress] Using config: compress=%s",
                    compress,
                )
                return compress

    # Case 3: Default
    logger.trace(
        "[resolve_compress] Using default: compress=%s",
        DEFAULT_COMPRESS,
    )
    return DEFAULT_COMPRESS
