# src/zipbundler/config/config_types.py

"""Configuration type definitions for zipbundler.

This module defines TypedDict schemas for all configuration structures.
"""

from pathlib import Path
from typing import Literal, TypedDict

from typing_extensions import NotRequired


# --- Literal types for enums ---

CompressionMethod = Literal["deflate", "stored", "bzip2", "lzma"]
OriginType = Literal["cli", "config", "gitignore"]


# --- Resolved path types ---


class PathResolved(TypedDict):
    """Resolved path with its root context.

    Used for files and directories that have been resolved to actual paths.
    The `path` can be absolute (overriding root) or relative to root.

    Fields:
        path: Absolute or relative-to-root path, or a glob pattern
        root: Canonical origin directory for path resolution (relative to cwd or config)
        origin: Where the path originated (cli or config)
        pattern: Original pattern before resolution (for logging/debugging)
    """

    path: Path | str
    root: Path
    origin: OriginType
    pattern: NotRequired[str]


class IncludeResolved(PathResolved):
    """Resolved include with optional custom destination.

    Extends PathResolved with an optional dest field to specify where
    the included file/directory should be placed in the output zip.

    Fields:
        dest: Optional override for target name/path in the zip file
    """

    dest: NotRequired[Path]


# --- Nested configuration types ---


class OutputConfig(TypedDict, total=False):
    """Output configuration for the zip file.

    Fields:
        path: Full path to output zip file (takes precedence over directory and name)
        directory: Output directory (default: "dist"). Used with name to generate path
        name: Optional name override for the zip file. When used with directory,
            generates {directory}/{name}.pyz
    """

    path: str
    directory: str
    name: str


class OptionsConfig(TypedDict, total=False):
    """Options configuration for zip file creation.

    Fields:
        shebang: Shebang line for the zip file. Can be:
            - True: Use default shebang
            - False: No shebang
            - str: Custom shebang path (with or without #!)
        main_guard: If True, wrap entry point in `if __name__ == "__main__":` guard
        compression: Compression method to use (default: "stored")
        compression_level: Compression level 0-9 (only valid with "deflate")
        respect_gitignore: If True, respect .gitignore patterns (default: True)
    """

    shebang: bool | str
    main_guard: bool
    compression: CompressionMethod
    compression_level: int  # 0-9
    respect_gitignore: bool


class OptionsConfigResolved(TypedDict):
    """Resolved options after merging CLI args, env vars, and config.

    All fields are required (will be populated with defaults during resolution).

    Fields:
        shebang: Resolved shebang (str path, or None if disabled)
        main_guard: Whether to wrap entry point in __main__ guard
        compression: Compression method to use
        compression_level: Compression level 0-9 (only for deflate)
        respect_gitignore: Whether to respect .gitignore patterns
        disable_build_timestamp: Whether to use placeholder instead of real
            timestamp (CLI-only + env var, never from config)
    """

    shebang: str | None  # None if --no-shebang, else string path
    main_guard: bool
    compression: CompressionMethod
    compression_level: int | None  # None unless using deflate
    respect_gitignore: bool
    disable_build_timestamp: bool


class MetadataConfig(TypedDict, total=False):
    """Metadata configuration for the zip file.

    Fields:
        display_name: Display name for the package
        description: Description of the package
        version: Version string
        author: Author information
        license: License information
    """

    display_name: str
    description: str
    version: str
    author: str
    license: str


# --- Include configuration types ---


class IncludeConfig(TypedDict):
    """Include configuration with optional destination.

    Fields:
        path: Path, glob pattern, or file name to include
        dest: Optional destination in the output zip
    """

    path: str
    dest: NotRequired[str]


# --- Root configuration type ---


class RootConfig(TypedDict, total=False):
    """Root configuration for zipbundler.

    Fields:
        packages: Required list of package paths or glob patterns to include
        exclude: Optional list of glob patterns for files/directories to exclude
        include: Optional list of additional files/directories to include
        entry_point: Optional entry point in format "module.path:function" or
            "module.path"
        output: Optional output configuration
        options: Optional options configuration
        metadata: Optional metadata configuration
    """

    packages: list[str]  # Required
    exclude: list[str]
    include: list[str | IncludeConfig]
    entry_point: str
    output: OutputConfig
    options: OptionsConfig
    metadata: MetadataConfig
