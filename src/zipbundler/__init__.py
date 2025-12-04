# src/zipbundler/__init__.py

"""Zipbundler — Bundle your packages into a runnable, importable zip.

Full developer API
==================
This package re-exports all non-private symbols from its submodules,
making it suitable for programmatic use, custom integrations, or plugins.
Anything prefixed with "_" is considered internal and may change.

Highlights:
    - create_archive()    → zipapp-compatible API
    - build_zip()         → Extended API for building zips
    - get_interpreter()    → Get interpreter from archive
    - watch()             → Watch for changes and rebuild
    - load_config()       → Load configuration file
    - validate_config()   → Validate configuration
"""

from pathlib import Path

from .actions import get_metadata
from .api import BuildResult, build_zip, create_archive, watch
from .build import get_interpreter
from .commands.validate import find_config, load_config, validate_config_structure
from .logs import getAppLogger
from .meta import PROGRAM_DISPLAY, PROGRAM_PACKAGE, PROGRAM_SCRIPT, Metadata


def validate_config(
    config_path: str | None = None,
    *,
    strict: bool = False,
    cwd: Path | None = None,
) -> bool:
    """Validate a configuration file.

    Args:
        config_path: Path to configuration file (searches for default if None)
        strict: Fail on warnings (default: False)
        cwd: Current working directory (default: current dir)

    Returns:
        True if config is valid, False otherwise

    Raises:
        FileNotFoundError: Config file not found
    """
    if cwd is None:
        cwd = Path.cwd().resolve()

    config_file = find_config(config_path, cwd)
    if not config_file:
        msg = "No configuration file found"
        raise FileNotFoundError(msg)

    config = load_config(config_file)
    is_valid, errors, warnings = validate_config_structure(config, cwd, strict=strict)

    if errors:
        logger = getAppLogger()
        for error in errors:
            logger.error("Config error: %s", error)

    if warnings and strict:
        logger = getAppLogger()
        for warning in warnings:
            logger.error("Config warning (strict mode): %s", warning)

    return is_valid


__all__ = [  # noqa: RUF022
    # api
    "BuildResult",
    "build_zip",
    "create_archive",
    "watch",
    # actions
    "get_metadata",
    # build
    "get_interpreter",
    # commands.validate
    "find_config",
    "load_config",
    "validate_config",
    # logs
    "getAppLogger",
    # meta
    "Metadata",
    "PROGRAM_DISPLAY",
    "PROGRAM_PACKAGE",
    "PROGRAM_SCRIPT",
]
