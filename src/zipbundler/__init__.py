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
    - load_and_validate_config() → Load and validate configuration
"""

from .actions import get_metadata
from .api import BuildResult, build_zip, create_archive, watch
from .build import get_interpreter
from .config import (
    find_config,
    load_and_validate_config,
    load_config,
)
from .logs import getAppLogger
from .meta import PROGRAM_DISPLAY, PROGRAM_PACKAGE, PROGRAM_SCRIPT, Metadata


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
    # config
    "find_config",
    "load_and_validate_config",
    "load_config",
    # logs
    "getAppLogger",
    # meta
    "Metadata",
    "PROGRAM_DISPLAY",
    "PROGRAM_PACKAGE",
    "PROGRAM_SCRIPT",
]
