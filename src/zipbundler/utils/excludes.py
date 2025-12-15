"""Utilities for resolving exclude configurations."""

import argparse
from pathlib import Path

from apathetic_utils import cast_hint

from zipbundler.config.config_types import OriginType, PathResolved
from zipbundler.logs import getAppLogger


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
