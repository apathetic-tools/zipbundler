"""Utilities for resolving include configurations."""

import argparse
from pathlib import Path

from apathetic_utils import cast_hint

from zipbundler.config.config_types import IncludeResolved, OriginType
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
    logger = getAppLogger()
    includes: list[IncludeResolved] = []

    for raw in include_list:
        if isinstance(raw, dict):
            # Object format: {"path": "...", "dest": "...", "type": "..."}
            raw_dict: dict[str, object] = cast_hint(dict[str, object], raw)
            path_obj = raw_dict.get("path", "")
            if not isinstance(path_obj, str):
                continue
            path_str: str = path_obj
            dest_obj = raw_dict.get("dest")
            dest_str: str | None = None
            if isinstance(dest_obj, str):
                dest_str = dest_obj

            # Extract type field (defaults to "file")
            type_obj = raw_dict.get("type")
            type_str: str | None = None
            if isinstance(type_obj, str):
                if type_obj not in ("file", "zip"):
                    logger.warning("Invalid include type: %s, using 'file'", type_obj)
                    type_str = "file"
                else:
                    type_str = type_obj

            inc = make_include_resolved(
                path_str, config_dir, "config", pattern=path_str
            )
            if dest_str:
                inc["dest"] = Path(dest_str)
            if type_str:  # pyright: ignore[reportTypedDictNotRequiredAccess]
                inc["type"] = type_str  # type: ignore[typeddict-item]
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
    3. If --add-zip is provided: append zip includes, use cwd as root
    4. If --add-include is provided: append to config includes, use cwd as root

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

    # Case 3: --add-zip (extend with zip type, not override)
    add_zip_arg: object = getattr(args, "add_zip", None)
    if add_zip_arg and isinstance(add_zip_arg, list):
        cli_list_zip = cast_hint(list[object], add_zip_arg)
        logger.trace(
            "[resolve_includes] Adding --add-zip items (%d items)",
            len(cli_list_zip),
        )
        # Create includes with type="zip", support PATH or PATH:dest syntax
        for raw in cli_list_zip:
            if isinstance(raw, str):
                inc, _ = parse_include_with_dest(raw, cwd)
                inc["type"] = "zip"
                includes.append(inc)

    # Case 4: --add-include (extend, not override)
    add_include_arg: object = getattr(args, "add_include", None)
    if add_include_arg and isinstance(add_include_arg, list):
        cli_list_add = cast_hint(list[object], add_include_arg)
        logger.trace(
            "[resolve_includes] Adding --add-include items (%d items)",
            len(cli_list_add),
        )
        includes.extend(_resolve_cli_includes(cli_list_add, cwd))

    return includes
