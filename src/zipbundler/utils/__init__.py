"""Utilities package for zipbundler.

Provides utilities for path resolution, include/exclude handling, compression,
gitignore patterns, and package discovery.
"""

from zipbundler.utils.compress import resolve_compress
from zipbundler.utils.discovered_packages import discover_installed_packages_roots
from zipbundler.utils.excludes import (
    make_exclude_resolved,
    resolve_excludes,
)
from zipbundler.utils.gitignore import (
    load_gitignore_patterns,
    resolve_gitignore,
)
from zipbundler.utils.includes import (
    make_include_resolved,
    parse_include_with_dest,
    resolve_includes,
)


__all__ = [
    "discover_installed_packages_roots",
    "load_gitignore_patterns",
    "make_exclude_resolved",
    "make_include_resolved",
    "parse_include_with_dest",
    "resolve_compress",
    "resolve_excludes",
    "resolve_gitignore",
    "resolve_includes",
]
